from dataclasses import dataclass, asdict

import subprocess as sp
import logging
import shlex
import json
import os

from .util import expand_globs

logger = logging.getLogger(__name__)


def new_job(script: str):
    return {
        'id': '', 'script': script, 'cwd': '', 'state': '', 'tries': 0,
    }


class Slurm:

    def __init__(self, sbatch='sbatch',  sacct='sacct'):
        self._sbatch_bin = sbatch
        self._sacct_bin = sacct

    def submit(self, *script: str, recovery: str = '', wait=False,
               timeout=None, opts='', max_tries=1, interval=10):
        """
        Submit scripts

        :param script: Script files to submit, can be glob patterns.
        :param recovery: Recovery file to store the state of the submitted scripts
        :param wait: If True, wait for the job to finish
        :param timeout: Timeout in seconds for waiting
        :param opts: Additional options for sbatch
        """
        jobs = {}
        if recovery and os.path.exists(recovery):
            with open(recovery, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
        logger.info('Recovery state: %s', jobs)

        for script_file in expand_globs(script):
            script_file = os.path.normpath(script_file)
            if script_file not in jobs:
                jobs[script_file] = new_job(script_file)

        while True:
            for script_file, job in jobs.items():
                ...



            # if '--parsable' not in opts:
            #     opts += ' --parsable'
            # submit_cmd = f'{self._sbatch_bin} {opts} {script_file}'

            # job = jobs.get(script_file, new_job(script_file))


            # if not job.id:
            #     cp = sp.run(submit_cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


