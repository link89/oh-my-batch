import fire

class OhMyBatch:

    def combo(self):
        from .combo import ComboMaker
        return ComboMaker

    def batch(self):
        from .batch import BatchMaker
        return BatchMaker


def main():
    fire.Fire(OhMyBatch)


if __name__ == '__main__':
    main()