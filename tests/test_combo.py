from oh_my_batch.combo import ComboMaker
from unittest import TestCase
import json
import os

TEST_DIR = os.path.dirname(__file__)

class TestCombo(TestCase):

    def test_sanity(self):
        combos = (ComboMaker()
            .add_var('VAR', 1, 2, 3)
            .add_var('VAR_BC', 4, 5, 6)
            .add_seq('SEQ', start=0, stop=10, step=1)
            .add_randint('RANDINT', n=5, a=1, b=10, seed=0)
            .add_rand('RAND_BC', n=5, a=1, b=10, seed=0)
            .add_files('FILES', f'tests/data/*.dummy.txt')
            .add_files_as_one('FILE_ONE', 'tests/data/*.dummy.txt')
            .set_broadcast('VAR_BC', 'RAND_BC')
            ._make_combos()
        )
        with open(f'{TEST_DIR}/golden/combos.json', 'r+', encoding='utf-8') as f:
            # json.dump(combos, f, indent=2)
            # f.seek(0)
            expected = json.load(f)
        l = 3 * 10 * 5 * 2
        self.assertEqual(len(combos), l)
        self.assertEqual(combos, expected)

    def test_add_files_as_one(self):

        pattern = 'tests/data/*.dummy.txt'
        test_items = [
            ('json-list', '["tests/data/2.dummy.txt", "tests/data/1.dummy.txt"]'),
            ('json-item',  '"tests/data/2.dummy.txt", "tests/data/1.dummy.txt"'),
        ]

        for fmt, expected in test_items:
            combo = ComboMaker()
            combo.add_files_as_one('FILE', pattern, format=fmt)
            self.assertEqual(combo._vars['FILE'][0], expected)