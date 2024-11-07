import fire

from .combo import ComboMaker


class OhMyBatch:

    def combo(self):
        return ComboMaker


def main():
    fire.Fire(OhMyBatch)


if __name__ == '__main__':
    main()