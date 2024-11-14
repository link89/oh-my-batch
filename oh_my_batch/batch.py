from oh_my_batch.util import split_list, ensure_dir
import shlex

class Batch:

    def __init__(self):
        self._work_dirs = []
        self._script_header = []
        self._script_bottom = []
        self._command = []

    def add_work_dir(self, *dir: str):
        """
        Add working directories
        """
        self._work_dirs.extend(dir)
        return self

    def add_header_file(self, file: str, encoding='utf-8'):
        """
        Add script header from files
        """
        with open(file, 'r', encoding=encoding) as f:
            self._script_header.append(f.read())
        return self

    def add_bottom_file(self, file: str, encoding='utf-8'):
        """
        Add script bottom from files
        """
        with open(file, 'r', encoding=encoding) as f:
            self._script_bottom.append(f.read())

    def add_command_file(self, file: str, encoding='utf-8'):
        """
        Add commands from files to run under every working directory
        """
        with open(file, 'r', encoding=encoding) as f:
            self._command.append(f.read())
        return self

    def add_command(self, *cmd: str):
        """
        add commands to run under every working directory
        """
        self._command.extend(cmd)
        return self

    def make(self, path: str, concurrency=1, encoding='utf-8'):
        """
        Make batch script files from the previous setup

        :param path: Path to save batch script files, use {i} to represent index
        :param concurrency: Number of concurrent commands to run
        """
        header = '\n'.join(self._script_header)
        bottom = '\n'.join(self._script_bottom)
        for i, work_dirs in enumerate(split_list(self._work_dirs, concurrency)):
            body = []
            work_dirs_arr = "\n".join(shlex.quote(w) for w in work_dirs)
            body.extend([
                f'work_dirs=({work_dirs_arr})',
                '',
                'for work_dir in "${work_dirs[@]}"; do',
                'pushd $work_dir',
                *self._command,
                'popd',
                'done'
            ])
            script = '\n'.join([header, *body, bottom])
            out_path = path.format(i=i)
            ensure_dir(out_path)
            with open(out_path, 'w', encoding=encoding) as f:
                f.write(script)
