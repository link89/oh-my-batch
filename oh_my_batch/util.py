from typing import List, Iterable
import subprocess as sp
import logging
import glob
import csv
import os


logger = logging.getLogger(__name__)


def expand_globs(patterns: Iterable[str], raise_invalid=False) -> List[str]:
    """
    Expand glob patterns in paths

    :param patterns: list of paths or glob patterns
    :param raise_invalid: if True, will raise error if no file found for a glob pattern
    :return: list of expanded paths
    """
    paths = []
    for pattern in patterns:
        result = glob.glob(pattern, recursive=True)
        if raise_invalid and len(result) == 0:
            raise FileNotFoundError(f'No file found for {pattern}')
        for p in result:
            if p not in paths:
                paths.append(p)
            else:
                logger.warning('path %s already exists in the list', p)
    return paths


def split_list(l, n):
    """
    Splits a list into n sub-lists.

    :param l: The list to be split.
    :param n: The number of sub-lists to create.
    :return: A list of sub-lists.
    """
    if n <= 0:
        raise ValueError("Number of sub-lists must be a positive integer")

    # Calculate the size of each sublist
    k, m = divmod(len(l), n)

    for i in range(n):
        start = i * k + min(i, m)
        end = (i + 1) * k + min(i + 1, m)
        if start == end:
            break
        yield l[start:end]


def ensure_dir(path: str):
    """
    Ensure the directory exists

    :param path: Path to directory or file.
    """
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def mode_translate(mode: str):
    """
    Translate mode in decimal to octal
    For example, convert 777 -> 0o777, 755 -> 0o755
    """
    return int(mode, 8)


def shell_run(cmd: str):
    """
    Run a shell command

    :param cmd: Command to run
    """
    return sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


def parse_csv(text: str, delimiter="|"):
    """
    Parse CSV text to list of dictionaries
    """
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return list(reader)


def log_cp(cp):
    """
    Log child process
    """
    log = f'Command: {cp.args}\nReturn code: {cp.returncode}'

    out = cp.stdout.decode('utf-8').strip()
    if out:
        log += f'\nSTDOUT:\n{out}'
    err = cp.stderr.decode('utf-8').strip()
    if err:
        log += f'\nSTDERR:\n{err}'
