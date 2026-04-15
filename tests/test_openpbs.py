import json
from unittest import TestCase
from unittest.mock import patch, MagicMock
from oh_my_batch.job import OpenPBS, JobState

class TestOpenPBS(TestCase):

    def setUp(self):
        self.pbs = OpenPBS()

    @patch('oh_my_batch.job.shell_run')
    def test_submit_job(self, mock_run):
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        mock_cp.stdout = b"1234.server\n"
        mock_run.return_value = mock_cp

        job = {'script': 'test.sh'}
        with patch('oh_my_batch.job.inject_exit_code_logging'):
            job_id = self.pbs._submit_job(job, '-q batch')
        
        self.assertEqual(job_id, "1234.server")
        mock_run.assert_called_once()
        self.assertIn('qsub -q batch', mock_run.call_args[0][0])

    @patch('oh_my_batch.job.shell_run')
    def test_update_state_qstat_json(self, mock_run):
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        qstat_output = {
            "Jobs": {
                "1234.server": {
                    "job_state": "R"
                },
                "1235.server": {
                    "job_state": "Q"
                },
                "1236.server": {
                    "job_state": "F"
                }
            }
        }
        mock_cp.stdout = json.dumps(qstat_output).encode('utf-8')
        mock_run.return_value = mock_cp

        jobs = [
            {'id': '1234.server', 'state': JobState.PENDING},
            {'id': '1235.server', 'state': JobState.PENDING},
            {'id': '1236.server', 'state': JobState.PENDING},
        ]
        
        updated_jobs = self.pbs._update_state(jobs)
        
        self.assertEqual(updated_jobs[0]['state'], JobState.RUNNING)
        self.assertEqual(updated_jobs[1]['state'], JobState.PENDING)
        self.assertEqual(updated_jobs[2]['state'], JobState.COMPLETED)

    def test_map_state(self):
        self.assertEqual(self.pbs._map_state('Q'), JobState.PENDING)
        self.assertEqual(self.pbs._map_state('R'), JobState.RUNNING)
        self.assertEqual(self.pbs._map_state('C'), JobState.COMPLETED)
        self.assertEqual(self.pbs._map_state('F'), JobState.COMPLETED)
        self.assertEqual(self.pbs._map_state('E'), JobState.RUNNING)
        self.assertEqual(self.pbs._map_state('XYZ'), JobState.UNKNOWN)

    @patch('oh_my_batch.job.shell_run')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_update_state_fallback_to_exitcode(self, mock_open, mock_exists, mock_run):
        # qstat returns nothing (job finished and cleared)
        mock_cp = MagicMock()
        mock_cp.returncode = 0
        mock_cp.stdout = b'{"Jobs": {}}'
        mock_run.return_value = mock_cp
        
        # .exitcode file exists and contains '0'
        mock_exists.side_effect = lambda p: p.endswith('.exitcode')
        mock_open.return_value.__enter__.return_value.read.return_value = "0"
        
        job = {'id': '1234.server', 'script': '/path/to/test.sh', 'state': JobState.PENDING}
        updated_jobs = self.pbs._update_state([job])
        
        self.assertEqual(updated_jobs[0]['state'], JobState.COMPLETED)
