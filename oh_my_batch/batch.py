import shlex
import os

from .util import split_list, ensure_dir, expand_globs, mode_translate
from .assets import get_asset


class BatchMaker:

    def __init__(self):
        self._work_dirs = []
        self._script_header = []
        self._script_bottom = []
        self._command = []

    def add_work_dir(self, *dir: str):
        """
        Add working directories

        :param dir: Directories to work on, can be glob patterns
        """
        self._work_dirs.extend(expand_globs(dir))
        return self

    def add_header_file(self, file: str, encoding='utf-8'):
        """
        Add script header from files

        :param file: File path
        :param encoding: File encoding
        """
        with open(file, 'r', encoding=encoding) as f:
            self._script_header.append(f.read())
        return self

    def add_bottom_file(self, file: str, encoding='utf-8'):
        """
        Add script bottom from files

        :param file: File path
        :param encoding: File encoding
        """
        with open(file, 'r', encoding=encoding) as f:
            self._script_bottom.append(f.read())

    def add_command_file(self, file: str, encoding='utf-8'):
        """
        Add commands from files to run under every working directory

        :param file: File path
        :param encoding: File encoding
        """
        with open(file, 'r', encoding=encoding) as f:
            self._command.append(f.read())
        return self

    def add_command(self, *cmd: str):
        """
        add commands to run under every working directory

        :param cmd: Commands to run, can be multiple
        """
        self._command.extend(cmd)
        return self

    def make(self, path: str, concurrency=1, encoding='utf-8', mode='755'):
        """
        Make batch script files from the previous setup

        :param path: Path to save batch script files, use {i} to represent index
        :param concurrency: Number of concurrent commands to run
        """
        # inject pre-defined functions
        self.add_header_file(get_asset('functions.sh'))

        header = '\n'.join(self._script_header)
        bottom = '\n'.join(self._script_bottom)
        for i, work_dirs in enumerate(split_list(self._work_dirs, concurrency)):
            body = []
            work_dirs_arr = "\n".join(shlex.quote(w) for w in work_dirs)
            body.extend([
                '[ -n "$PBS_O_WORKDIR" ] && cd $PBS_O_WORKDIR  # fix PBS',
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
            os.chmod(out_path, mode_translate(str(mode)))
