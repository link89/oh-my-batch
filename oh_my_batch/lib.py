from itertools import product
from string import Template
import random
import glob 
import os


class ComboMaker:

    def __init__(self, seed: int=None):
        """
        ComboMaker constructor

        :param seed: Seed for random number generator
        """
        self._product_vars = {}
        self._broadcase_vars = {}
        if seed is not None:
            random.seed(seed)

    def add_seq(self, key: str, start: int, stop: int, step: int=1, broadcast=False):
        """
        Add a variable with sequence of integer values

        :param key: Variable name
        :param start: Start value
        :param stop: Stop value
        :param step: Step
        :param broadcast: If True, values are broadcasted, otherwise they are producted when making combos
        """
        args = list(range(start, stop, step))
        self.add_var(key, *args, broadcast=broadcast)
        return self
    
    def add_randint(self, key: str, n: int, a: int, b: int, broadcast=False, seed=None):
        """
        Add a variable with random integer values

        :param key: Variable name
        :param n: Number of values
        :param a: Lower bound
        :param b: Upper bound
        :param broadcast: If True, values are broadcasted, otherwise they are producted when making combos
        :param seed: Seed for random number generator
        """
        if seed is not None:
            random.seed(seed)
        args = [random.randint(a, b) for _ in range(n)]
        self.add_var(key, *args, broadcast=broadcast)
        return self
    
    def add_rand(self, key: str, n: int, a: float, b: float, broadcast=False, seed=None):
        """
        Add a variable with random float values

        :param key: Variable name
        :param n: Number of values
        :param a: Lower bound
        :param b: Upper bound
        :param broadcast: If True, values are broadcasted, otherwise they are producted when making combos
        :param seed: Seed for random number generator
        """
        if seed is not None:
            random.seed(seed)
        args = [random.uniform(a, b) for _ in range(n)]
        self.add_var(key, *args, broadcast=broadcast)
        return self
    
    def add_files(self, key: str, path: str, broadcast=False):
        """
        Add a variable with files by glob pattern
        For example, suppose there are 1.txt, 2.txt, 3.txt in data directory,
        then calling add_files('DATA_FILE', 'data/*.txt') will add list ["data/1.txt", "data/2.txt", "data/3.txt"]
        to the variable DATA_FILE.

        :param key: Variable name
        :param path: Path to files, can include glob pattern
        :param broadcast: If True, values are broadcasted, otherwise they are producted when making combos
        """
        args = glob.glob(path)
        if not args:
            raise ValueError(f"No files found for {path}")
        self.add_var(key, *args, broadcast=broadcast)
        return self

    def add_files_as_one(self, key: str, path: str, broadcast=False, sep=' '):
        """
        Add a variable with files by glob pattern as one string
        Unlike add_files, this function joins the files with a delimiter.
        For example, suppose there are 1.txt, 2.txt, 3.txt in data directory,
        then calling add_files_as_one('DATA_FILE', 'data/*.txt') will add string "data/1.txt data/2.txt data/3.txt"
        to the variable DATA_FILE.

        :param key: Variable name
        :param path: Path to files, can include glob pattern
        :param broadcast: If True, values are broadcasted, otherwise they are producted when making combos
        :param sep: Separator to join files
        """
        args = glob.glob(path)
        if not args:
            raise ValueError(f"No files found for {path}")
        self.add_var(key, sep.join(args), broadcast=broadcast)
        return self

    def add_var(self, key: str, *args, broadcast=False):
        if key == 'i':
            raise ValueError("Variable name 'i' is reserved")

        if broadcast:
            if key in self._product_vars:
                raise ValueError(f"Variable {key} already defined as product variable")
            self._broadcase_vars.setdefault(key, []).extend(args)
        else:
            if key in self._broadcase_vars:
                raise ValueError(f"Variable {key} already defined as broadcast variable")
            self._product_vars.setdefault(key, []).extend(args)
        return self

    def shuffle(self, *keys: str, seed=None):
        """
        Shuffle variables
        :param keys: Variable names to shuffle
        :param seed: Seed for random number generator
        """
        if seed is not None:
            random.seed(seed)

        for key in keys:
            if key in self._product_vars:
                random.shuffle(self._product_vars[key])
            elif key in self._broadcase_vars:
                random.shuffle(self._broadcase_vars[key])
            else:
                raise ValueError(f"Variable {key} not found")
        return self

    def make_files(self, template: str, dest: str, delimiter='$'):
        _delimiter = delimiter

        class _Template(Template):
            delimiter = _delimiter

        combos = self._make_combos()
        for i, combo in enumerate(combos):
            with open(template, 'r') as f:
                template_text = f.read()
            text = _Template(template_text).safe_substitute(combo)
            _dest = dest.format(i=i, **combo)
            os.makedirs(os.path.dirname(_dest), exist_ok=True)
            with open(_dest, 'w') as f:
                f.write(text)
        return self

    def _make_combos(self):
        keys = self._product_vars.keys()
        values_list = product(*self._product_vars.values())
        combos = [ dict(zip(keys, values)) for values in values_list ]
        for i, combo in enumerate(combos):
            for k, v in self._broadcase_vars.items():
                combo[k] = v[i % len(v)]
        return combos
    

if __name__ == '__main__':
    import fire
    fire.Fire(ComboMaker)