from typing import List

import logging
import json
import time
import os
import re

from .util import expand_globs, shell_run, parse_csv, ensure_dir, log_cp


logger = logging.getLogger(__name__)


class JobState:
    NULL = 0
    PENDING = 1
    RUNNING = 2
    CANCELLED = 3
    COMPLETED = 4
    FAILED = 5
    UNKNOWN = 6

    @classmethod
    def is_terminal(cls, state: int):
        return state in (JobState.NULL, JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED)

    @classmethod
    def is_success(cls, state: int):
        return state == JobState.COMPLETED


def new_job(script: str):
    return {
        'id': '', 'script': script, 'state': JobState.NULL, 'tries': 0,
    }


class BaseJobManager:

    def submit(self, *script: str, recovery: str = '', wait=False,
               timeout=None, opts='', max_tries=1, interval=10):
        """
        Submit scripts

        :param script: Script files to submit, can be glob patterns.
        :param recovery: Recovery file to store the state of the submitted scripts
        :param wait: If True, wait for the job to finish
        :param timeout: Timeout in seconds for waiting
        :param opts: Additional options for submit command
        :param max_tries: Maximum number of tries for each job
        :param interval: Interval in seconds for checking job status
        """
        jobs = []
        if recovery and os.path.exists(recovery):
            with open(recovery, 'r', encoding='utf-8') as f:
                jobs = json.load(f)

        recover_scripts = set(j['script'] for j in jobs)
        logger.info('Scripts in recovery files: %s', recover_scripts)

        scripts = set(norm_path(s) for s in expand_globs(script, raise_invalid=True))
        logger.info('Scripts to submit: %s', scripts)

        for script_file in scripts:
            if script_file not in recover_scripts:
                jobs.append(new_job(script_file))

        current = time.time()
        while True:
            jobs = self._update_jobs(jobs, max_tries, opts)
            if recovery:
                ensure_dir(recovery)
                with open(recovery, 'w', encoding='utf-8') as f:
                    json.dump(jobs, f, indent=2)

            if not wait:
                break

            # stop if all jobs are terminal and no job to be submitted
            if (all(JobState.is_terminal(j['state']) for j in jobs) and
                    not any(should_submit(j, max_tries) for j in jobs)):
                break

            if timeout and time.time() - current > timeout:
                logger.error('Timeout, current state: %s', jobs)
                break

            time.sleep(interval)

        raise_err = False
        for job in jobs:
            if not JobState.is_terminal(job['state']):
                logger.warning('Job %s is running, current state: %s', job['script'], job['state'])
                raise_err = True
            elif not JobState.is_success(job['state']):
                logger.error('Job %s failed', job['script'])
                raise_err = True
        if raise_err and wait:
            raise RuntimeError('Some jobs failed or not finished yet')

    def wait(self, *job_ids, timeout=None, interval=10):
        """
        Wait for jobs to finish

        :param job_ids: Job ids to wait for
        :param timeout: Timeout in seconds
        :param interval: Interval in seconds for checking job status
        """
        current = time.time()
        while True:
            jobs = [{'id': j, 'state': JobState.NULL} for j in job_ids]
            jobs = self._update_state(jobs)
            if all(JobState.is_terminal(j['state']) for j in jobs):
                break
            if timeout and time.time() - current > timeout:
                logger.error('Timeout, current state: %s', jobs)
                break
            time.sleep(interval)

    def _update_jobs(self, jobs: List[dict], max_tries: int, submit_opts: str):
        jobs = self._update_state(jobs)

        # check if there are jobs to be (re)submitted
        for job in jobs:
            if should_submit(job, max_tries):
                job['tries'] += 1
                job['id'] = ''
                job['state'] = JobState.NULL
                # remove exit

                job_id = self._submit_job(job, submit_opts)
                if job_id:
                    job['state'] = JobState.PENDING
                    job['id'] = job_id
                    logger.info('Job %s submitted', job['id'])
                else:
                    job['state'] = JobState.FAILED
                    logger.error('Failed to submit job %s', job['script'])
        return jobs

    def _update_state(self, jobs: List[dict]):
        raise NotImplementedError

    def _submit_job(self, job: dict, submit_opts: str):
        raise NotImplementedError


class Slurm(BaseJobManager):
    def __init__(self, sbatch='sbatch', sacct='sacct', squeue='squeue'):
        self._sbatch_bin = sbatch
        self._sacct_bin = sacct
        self._squeue_bin = squeue

    def _update_state(self, jobs: List[dict]):
        jobs_with_id = [j for j in jobs if j['id']]
        if not jobs_with_id:
            return jobs

        missing_jobs = self._update_state_from_sacct(jobs_with_id)
        if not missing_jobs:
            return jobs

        missing_jobs = self._update_state_from_squeue(missing_jobs)
        if not missing_jobs:
            return jobs

        self._update_state_from_exitcode(missing_jobs)
        return jobs

    def _update_state_from_sacct(self, jobs: List[dict]):
        job_ids = [j['id'] for j in jobs]
        query_cmd = f'{self._sacct_bin} -X -P --format=JobID,State -j {",".join(job_ids)}'
        cp = shell_run(query_cmd)

        if cp.returncode != 0:
            logger.warning('Failed to query job status from sacct, using fallback: %s', log_cp(cp))
            return jobs

        out = cp.stdout.decode('utf-8')
        logger.debug('sacct output:\n%s', out)
        new_state_from_sacct = parse_csv(out)

        found_job_ids = {row['JobID'] for row in new_state_from_sacct}
        missing_jobs = []

        for job in jobs:
            if job['id'] in found_job_ids:
                for row in new_state_from_sacct:
                    if job['id'] == row['JobID']:
                        job['state'] = self._map_state(row['State'])
                        if job['state'] == JobState.UNKNOWN:
                            logger.warning('Unknown job %s state from sacct: %s', row['JobID'], row['State'])
                        break
            else:
                logger.warning('Job %s not found in sacct output', job['id'])
                missing_jobs.append(job)
        return missing_jobs

    def _update_state_from_squeue(self, jobs: List[dict]):
        new_state_from_squeue = {}
        squeue_cmd = f'{self._squeue_bin} -h -o "%A %t"'  # JobID State
        cp = shell_run(squeue_cmd)

        if cp.returncode == 0:
            out = cp.stdout.decode('utf-8').strip()
            logger.debug('squeue output:\n%s', out)
            if out:
                for line in out.split('\n'):
                    parts = line.split()
                    if len(parts) == 2:
                        new_state_from_squeue[parts[0]] = parts[1]
        else:
            logger.error('Failed to query job status from squeue: %s', log_cp(cp))

        missing_jobs = []
        for job in jobs:
            if job['id'] in new_state_from_squeue:
                job['state'] = self._map_squeue_state(new_state_from_squeue[job['id']])
            else:
                missing_jobs.append(job)
        return missing_jobs

    def _update_state_from_exitcode(self, jobs: List[dict]):
        for job in jobs:
            exit_code_file = os.path.abspath(job['script']) + '.exitcode'
            if os.path.exists(exit_code_file):
                try:
                    with open(exit_code_file, 'r', encoding='utf-8') as f:
                        exit_code = f.read().strip()
                    if exit_code == '0':
                        job['state'] = JobState.COMPLETED
                    else:
                        job['state'] = JobState.FAILED
                        logger.warning('Job %s failed with exit code %s found in %s', job['id'], exit_code, exit_code_file)
                except Exception as e:
                    logger.error("Error reading exit code file %s for job %s: %s", exit_code_file, job['id'], e)
                    job['state'] = JobState.FAILED
            else:
                job['state'] = JobState.FAILED
                logger.error('Job %s not found in sacct, squeue, and .exitcode file not found at %s', job['id'], exit_code_file)

    def _submit_job(self, job:dict, submit_opts:str):
        submit_cmd = f'{self._sbatch_bin} {submit_opts} {job["script"]}'
        cp = shell_run(submit_cmd)
        if cp.returncode != 0:
            logger.error('Failed to submit job: %s', log_cp(cp))
            return ''
        out = cp.stdout.decode('utf-8')
        job_id  = self._parse_job_id(out)
        if not job_id:
            raise ValueError(f'Unexpected sbatch output: {out}')
        return job_id

    def _map_squeue_state(self, state: str):
        if state in ('PD',):
            return JobState.PENDING
        if state in ('R', 'CG', 'CF'):
            return JobState.RUNNING
        if state in ('CA', 'F', 'TO', 'NF', 'RV', 'SE'):
            return JobState.FAILED
        if state in ('CD',):
            return JobState.COMPLETED
        return JobState.UNKNOWN

    def _map_state(self, state: str):
        if state.startswith('CANCELLED'):
            return JobState.CANCELLED
        return {
            'PENDING': JobState.PENDING,
            'RUNNING': JobState.RUNNING,
            'COMPLETED': JobState.COMPLETED,
            'FAILED': JobState.FAILED,
            'OUT_OF_MEMORY': JobState.FAILED,
            'TIMEOUT': JobState.FAILED,
        }.get(state, JobState.UNKNOWN)

    def _parse_job_id(self, output: str):
        """
        Parse job id from sbatch output
        """
        m = re.search(r'\d+', output)
        return m.group(0) if m else ''


def should_submit(job: dict, max_tries: int):
    state: int = job['state']
    if not JobState.is_terminal(state):
        return False
    if job['tries'] >= max_tries:
        return False
    return state != JobState.COMPLETED


def norm_path(path: str):
    return os.path.normpath(path)
