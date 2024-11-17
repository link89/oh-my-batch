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


    def _update_jobs(self, jobs: List[dict], max_tries: int, submit_opts: str):
        jobs = self._update_state(jobs)

        # check if there are jobs to be (re)submitted
        for job in jobs:
            if should_submit(job, max_tries):
                job['tries'] += 1
                job['id'] = ''
                job['state'] = JobState.NULL
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
    def __init__(self, sbatch='sbatch',  sacct='sacct'):
        self._sbatch_bin = sbatch
        self._sacct_bin = sacct

    def _update_state(self, jobs: List[dict]):
        job_ids = [j['id'] for j in jobs if j['id']]
        if job_ids:
            query_cmd = f'{self._sacct_bin} -X -P --format=JobID,JobName,State -j {",".join(job_ids)}'
            cp = shell_run(query_cmd)
            if cp.returncode != 0:
                logger.error('Failed to query job status: %s', log_cp(cp))
                return jobs
            out = cp.stdout.decode('utf-8')
            logger.info('Job status:\n%s', out)
            new_state = parse_csv(out)
        else:
            new_state = []

        for job in jobs:
            if not job['id']:
                continue
            for row in new_state:
                if job['id'] == row['JobID']:
                    job['state'] = self._map_state(row['State'])
                    if job['state'] == JobState.UNKNOWN:
                        logger.warning('Unknown job %s state: %s',row['JobID'], row['State'])
                    break
            else:
                logger.error('Job %s not found in sacct output', job['id'])
        return jobs 

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
