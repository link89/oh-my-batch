from oh_my_batch.combo import ComboMaker
from unittest import TestCase

class TestComboCompute(TestCase):
    def test_compute(self):
        maker = ComboMaker()
        maker.add_var('TEMP', 300, 400, 600)
        maker.compute('X_TEMP', '1200 // TEMP')
        combos = maker._make_combos()

        self.assertEqual(len(combos), 3)
        self.assertEqual(combos[0]['TEMP'], 300)
        self.assertEqual(combos[0]['X_TEMP'], 4)
        self.assertEqual(combos[1]['TEMP'], 400)
        self.assertEqual(combos[1]['X_TEMP'], 3)
        self.assertEqual(combos[2]['TEMP'], 600)
        self.assertEqual(combos[2]['X_TEMP'], 2)

    def test_compute_multiple_vars(self):
        maker = ComboMaker()
        maker.add_var('A', 1, 2)
        maker.add_var('B', 10, 20)
        maker.compute('C', 'A + B')
        combos = maker._make_combos()

        self.assertEqual(len(combos), 4)
        # 1+10, 1+20, 2+10, 2+20
        results = [c['C'] for c in combos]
        self.assertIn(11, results)
        self.assertIn(21, results)
        self.assertIn(12, results)
        self.assertIn(22, results)
