from unittest import TestCase
from oh_my_batch import util

class TestUtil(TestCase):

    def test_split_list(self):
        l = list(range(10))
        n = 3
        result = list(util.split_list(l, n))
        self.assertEqual(len(result), n)
        self.assertEqual(len(result[0]), 4)
        self.assertEqual(len(result[1]), 3)
        self.assertEqual(len(result[2]), 3)
        self.assertEqual(result[0], [0, 1, 2, 3])
        self.assertEqual(result[1], [4, 5, 6])
        self.assertEqual(result[2], [7, 8, 9])

        n = 20
        result = list(util.split_list(l, n))
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], [0])
        self.assertEqual(result[1], [1])
        self.assertEqual(result[9], [9])

    def test_mode_translate(self):
        self.assertEqual(util.mode_translate('777'), 0o777)
        self.assertEqual(util.mode_translate('755'), 0o755)
        self.assertEqual(util.mode_translate('700'), 0o700)
        self.assertEqual(util.mode_translate('644'), 0o644)
        self.assertEqual(util.mode_translate('600'), 0o600)

    def test_inject_exit_code_logging(self):
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("echo 'hello world'\n")
            script_path = f.name

        try:
            exit_code_path = script_path + '.exitcode'
            util.inject_exit_code_logging(script_path, exit_code_path)

            with open(script_path, 'r') as f:
                content = f.read()

            self.assertIn("echo 'hello world'", content)
            self.assertIn("LOG EXIT CODE BY OH MY BATCH", content)
            self.assertIn(f'echo $EXIT_CODE > "{exit_code_path}"', content)

            # test idempotency
            util.inject_exit_code_logging(script_path, exit_code_path)
            with open(script_path, 'r') as f:
                content = f.read()
            # make sure it is not duplicated.
            self.assertEqual(content.count("LOG EXIT CODE BY OH MY BATCH"), 3)

        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
