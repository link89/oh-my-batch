import logging
import fire


class JobCli:

    def slurm(self):
        from .job import Slurm
        return Slurm

    def openpbs(self):
        from .job import OpenPBS
        return OpenPBS


class OhMyBatch:

    def combo(self):
        from .combo import ComboMaker
        return ComboMaker

    def batch(self):
        from .batch import BatchMaker
        return BatchMaker

    def job(self):
        return JobCli()

    def shell(self):
        from .shell import Shell
        return Shell()


def main():
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO)
    fire.Fire(OhMyBatch)
