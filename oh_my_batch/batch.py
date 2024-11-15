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

    def add_work_dirs(self, *dir: str):
        """
        Add working directories

        :param dir: Directories to work on, can be glob patterns
        """
        self._work_dirs.extend(expand_globs(dir))
        return self

    def add_header_files(self, *file: str, encoding='utf-8'):
        """
        Add script header from files

        :param file: File path
        :param encoding: File encoding
        """
        self._script_header.extend(load_files(*file, encoding=encoding))
        return self

    def add_headers(self, *header: str):
        """
        Add script header

        :param header: Header lines
        """
        self._script_header.extend(header)
        return self

    def add_bottom_files(self, *file: str, encoding='utf-8'):
        """
        Add script bottom from files

        :param file: File path
        :param encoding: File encoding
        """
        self._script_bottom.extend(load_files(*file, encoding=encoding))
        return self

    def add_bottoms(self, *bottom: str):
        """
        Add script bottom

        :param bottom: Bottom lines
        """
        self._script_bottom.extend(bottom)
        return self

    def add_cmd_files(self, *file: str, encoding='utf-8'):
        """
        Add commands from files to run under every working directory

        :param file: File path
        :param encoding: File encoding
        """
        self._command.extend(load_files(*file, encoding=encoding))
        return self

    def add_cmds(self, *cmd: str):
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
        :param concurrency: Number of scripts to to make
        """
        # inject pre-defined functions
        self.add_header_files(get_asset('functions.sh'))

        header = '\n'.join(self._script_header)
        bottom = '\n'.join(self._script_bottom)
        for i, work_dirs in enumerate(split_list(self._work_dirs, concurrency)):
            body = []
            work_dirs_arr = "\n".join(shlex.quote(w) for w in work_dirs)
            body.extend([
                '[ -n "$PBS_O_WORKDIR" ] && cd $PBS_O_WORKDIR  # fix PBS',
                f'WORK_DIRS=({work_dirs_arr})',
                '',
                'for WORK_DIR in "${WORK_DIRS[@]}"; do',
                'pushd $WORK_DIR',
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


def load_files(*file, encoding='utf-8', raise_invalid=False):
    """
    Load files from paths

    :param files: List of file paths
    :return: List of file contents
    """
    result = []
    for file in expand_globs(file, raise_invalid=raise_invalid):
        with open(file, 'r', encoding=encoding) as f:
            result.append(f.read())
    return result