from itertools import product
from string import Template
import os
import random
import shutil


class TaskBuilder:

    def __init__(self):
        self.product_vars = {}
        self.broadcase_vars = {}
    
    def add_randint(self, name: str, n: int, a: int, b: int, broadcast=False):
        args = [random.randint(a, b) for _ in range(n)]
        self.add_var(name, *args, broadcast=broadcast)
        return self
    
    def add_rand(self, name: str, n: int, a=0, b=1, broadcast=False):
        args = [random.uniform(a, b) for _ in range(n)]
        self.add_var(name, *args, broadcast=broadcast)
        return self
    
    def add_files(self, name: str, glob: str, broadcast=False):
        return self
    
    def add_files_as_one(self, name: str, glob: str, broadcast=False, sep=' '):
        return self

        
    def add_var(self, name: str, *args, broadcast=False):
        if name == 'i':
            raise ValueError("Variable name 'i' is reserved")

        if broadcast:
            if name in self.product_vars:
                raise ValueError(f"Variable {name} already defined as product variable")
            self.broadcase_vars.setdefault(name, []).extend(args)
        else:
            if name in self.broadcase_vars:
                raise ValueError(f"Variable {name} already defined as broadcast variable")
            self.product_vars.setdefault(name, []).extend(args)
        return self

    def make_files_from_template(self, template_file: str, dest: str, delimiter='$'):
        _delimiter = delimiter

        class _Template(Template):
            delimiter = _delimiter

        vars_list = self._get_vars_list()
        for i, vars in enumerate(vars_list):
            with open(template_file, 'r') as f:
                template = f.read()
            text = _Template(template).safe_substitute(vars)
            _dest = dest.format(i=i, **vars)
            os.makedirs(os.path.dirname(_dest), exist_ok=True)
            with open(_dest, 'w') as f:
                f.write(text)
        return self
    
    def copy_files(self, src: str, dest: str):
        vars_list = self._get_vars_list()
        for i, vars in enumerate(vars_list):
            _src = src.format(i=i, **vars)
            _dest = dest.format(i=i, **vars)
            os.makedirs(os.path.dirname(_dest), exist_ok=True)
            os.system(f'cp -r {src} {dest}')  # TODO: use shutil
        return self
    

    def _get_vars_list(self):
        keys = self.product_vars.keys()
        values_list = product(*self.product_vars.values())
        vars_list = [ dict(zip(keys, values)) for values in values_list ]
        for i, vars in enumerate(vars_list):
            for k, v in self.broadcase_vars.items():
                vars[k] = v[i % len(v)]
        return vars_list


if __name__ == '__main__':
    import fire
    fire.Fire(TaskBuilder)