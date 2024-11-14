import os

DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset(rel_path: str):
    return os.path.join(DIR, rel_path)