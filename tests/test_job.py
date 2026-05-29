import json
import os
import tempfile
from unittest import TestCase

from oh_my_batch.job import BaseJobManager, JobState, should_submit


class DummyJobManager(BaseJobManager):
    def __init__(self):
        self.submitted_jobs = []

    def _update_state(self, jobs):
        return jobs

    def _submit_job(self, job, submit_opts: str):
        self.submitted_jobs.append((job['script'], submit_opts))
        return 'submitted-1'

class TestJob(TestCase):

    def test_should_submit(self):
        max_tries = 3
        test_items = [
            ({'state': JobState.NULL, 'tries': 0}, True),
            ({'state': JobState.NULL, 'tries': 1}, True),
            ({'state': JobState.NULL, 'tries': 2}, True),
            ({'state': JobState.NULL, 'tries': 3}, False),

            ({'state': JobState.PENDING, 'tries': 0}, False),
            ({'state': JobState.RUNNING, 'tries': 0}, False),
            ({'state': JobState.UNKNOWN, 'tries': 0}, False),

            ({'state': JobState.COMPLETED, 'tries': 0}, False),

            ({'state': JobState.CANCELLED, 'tries': 0}, True),
            ({'state': JobState.FAILED, 'tries': 1}, True),
            ({'state': JobState.FAILED, 'tries': 2}, True),
            ({'state': JobState.FAILED, 'tries': 3}, False),
        ]

        for item in test_items:
            self.assertEqual(should_submit(item[0], max_tries), item[1], msg=item[0])

    def test_submit_logs_recovered_job_states(self):
        manager = DummyJobManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, 'job.sh')
            recovery_path = os.path.join(tmpdir, 'recovery.json')

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write('#!/bin/sh\nexit 0\n')

            with open(recovery_path, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        'id': '1234',
                        'script': script_path,
                        'state': JobState.COMPLETED,
                        'tries': 1,
                    }
                ], f)

            with self.assertLogs('oh_my_batch.job', level='INFO') as logs:
                manager.submit(script_path, recovery=recovery_path)

        self.assertEqual(manager.submitted_jobs, [])
        log_output = '\n'.join(logs.output)
        self.assertIn('Jobs recovered from', log_output)
        self.assertIn("COMPLETED(4)", log_output)
        self.assertIn('Requested scripts', log_output)
