import fire

from .combo import ComboMaker


class OhMyBatch:

    def combo(self):
        return ComboMaker
    

if __name__ == '__main__':
    fire.Fire(OhMyBatch)    