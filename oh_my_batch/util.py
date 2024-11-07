from typing import List, Iterable
import glob


def expand_globs(patterns: Iterable[str], raise_invalid=False) -> List[str]:
    """
    Expand glob patterns in paths

    :param patterns: list of paths or glob patterns
    :param raise_invalid: if True, will raise error if no file found for a glob pattern
    :return: list of expanded paths
    """
    paths = []
    for pattern in patterns:
        result = glob.glob(pattern, recursive=True) if '*' in pattern else [pattern]
        if raise_invalid and len(result) == 0:
            raise FileNotFoundError(f'No file found for {pattern}')
        for p in result:
            if p not in paths:
                paths.append(p)
            else:
                print(f'path {p} already exists in the list')
    return paths