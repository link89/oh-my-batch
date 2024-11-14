import fire

class JobCli:

    def slurm(self):
        from .job import Slurm
        return Slurm


class OhMyBatch:

    def combo(self):
        from .combo import ComboMaker
        return ComboMaker

    def batch(self):
        from .batch import BatchMaker
        return BatchMaker

    def job(self):
        return JobCli()


def main():
    fire.Fire(OhMyBatch)
