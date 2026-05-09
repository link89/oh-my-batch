import os
import tempfile
from unittest import TestCase

from oh_my_batch.shell import Shell


class TestShell(TestCase):

    def test_try_file_returns_first_existing_path(self):
        shell = Shell()

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = os.path.join(temp_dir, 'input.txt')
            with open(existing_file, 'w'):
                pass

            result = shell.try_file(
                os.path.join(temp_dir, 'missing.txt'),
                existing_file,
                temp_dir,
            )

        self.assertEqual(result, existing_file)

    def test_try_file_returns_original_glob_when_it_matches(self):
        shell = Shell()

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = os.path.join(temp_dir, 'input.txt')
            with open(existing_file, 'w'):
                pass

            pattern = os.path.join(temp_dir, '*.txt')
            result = shell.try_file(
                os.path.join(temp_dir, 'missing.txt'),
                pattern,
            )

        self.assertEqual(result, pattern)

    def test_try_file_exits_when_no_path_exists(self):
        shell = Shell()

        with tempfile.TemporaryDirectory() as temp_dir:
            missing_file = os.path.join(temp_dir, 'missing.txt')
            missing_dir = os.path.join(temp_dir, 'missing-dir')

            with self.assertRaises(SystemExit) as error:
                shell.try_file(missing_file, missing_dir)

        self.assertEqual(error.exception.code, 1)