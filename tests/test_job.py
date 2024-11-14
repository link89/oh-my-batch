from unittest import TestCase
from oh_my_batch.job import should_submit, JobState

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
