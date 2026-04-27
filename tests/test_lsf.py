from unittest import TestCase
from unittest.mock import MagicMock, patch

from oh_my_batch.job import LSF, JobState


class TestLSF(TestCase):

    def setUp(self):
        self.lsf = LSF()

    @patch('oh_my_batch.job.shell_run')
    def test_submit_job(self, mock_run):
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        mock_cp.stdout = b'Job <1234> is submitted to default queue <normal>.\n'
        mock_run.return_value = mock_cp

        job = {'script': 'test.sh'}
        with patch('oh_my_batch.job.inject_exit_code_logging'):
            job_id = self.lsf._submit_job(job, '-q normal')

        self.assertEqual(job_id, '1234')
        mock_run.assert_called_once()
        self.assertIn('bsub -q normal < ', mock_run.call_args[0][0])

    @patch('oh_my_batch.job.shell_run')
    def test_update_state_bjobs(self, mock_run):
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        mock_cp.stdout = b'1234 RUN\n1235 PEND\n1236 DONE\n1237 EXIT\n'
        mock_run.return_value = mock_cp

        jobs = [
            {'id': '1234', 'state': JobState.PENDING},
            {'id': '1235', 'state': JobState.PENDING},
            {'id': '1236', 'state': JobState.PENDING},
            {'id': '1237', 'state': JobState.PENDING},
        ]

        updated_jobs = self.lsf._update_state(jobs)

        self.assertEqual(updated_jobs[0]['state'], JobState.RUNNING)
        self.assertEqual(updated_jobs[1]['state'], JobState.PENDING)
        self.assertEqual(updated_jobs[2]['state'], JobState.COMPLETED)
        self.assertEqual(updated_jobs[3]['state'], JobState.FAILED)

    def test_map_state(self):
        self.assertEqual(self.lsf._map_state('PEND'), JobState.PENDING)
        self.assertEqual(self.lsf._map_state('RUN'), JobState.RUNNING)
        self.assertEqual(self.lsf._map_state('DONE'), JobState.COMPLETED)
        self.assertEqual(self.lsf._map_state('EXIT'), JobState.FAILED)
        self.assertEqual(self.lsf._map_state('UNKWN'), JobState.UNKNOWN)

    @patch('oh_my_batch.job.shell_run')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_update_state_fallback_to_exitcode(self, mock_open, mock_exists, mock_run):
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        mock_cp.stdout = b''
        mock_run.return_value = mock_cp

        mock_exists.side_effect = lambda path: path.endswith('.exitcode')
        mock_open.return_value.__enter__.return_value.read.return_value = '0'

        job = {'id': '1234', 'script': '/path/to/test.sh', 'state': JobState.PENDING}
        updated_jobs = self.lsf._update_state([job])

        self.assertEqual(updated_jobs[0]['state'], JobState.COMPLETED)