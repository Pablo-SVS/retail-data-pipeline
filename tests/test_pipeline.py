import tempfile
from pathlib import Path
import unittest
import pandas as pd
from pipeline import COLUMNS, transform, load


class PipelineTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([
            ['100', 'A', 'Item', 2, '2011-01-01', 1.25, 123, 'UK'],
            ['100', 'A', 'Item', 2, '2011-01-01', 1.25, 123, 'UK'],
            ['C101', 'A', 'Item', -1, '2011-01-02', 1.25, 123, 'UK'],
            ['102', 'B', None, 3, '2011-01-03', 0.001, None, 'UK'],
            ['103', 'B', 'Bad price', 1, '2011-01-03', 0, None, 'UK'],
            ['104', 'B', 'Bad date', 1, 'invalid', 1, None, 'UK'],
        ], columns=COLUMNS)

    def test_conservation_credits_duplicates_missing_customer_precision(self):
        clean, rejected, report = transform(self.frame())
        self.assertEqual((len(clean), len(rejected)), (4, 2))
        self.assertEqual(report['duplicate_candidate_rows_preserved'], 1)
        self.assertEqual(report['accepted_rows_without_customer'], 1)
        self.assertEqual(report['gross_sales_mills'], 5003)
        self.assertEqual(report['credits_mills'], 1250)
        self.assertEqual(report['net_movement_mills'], 3753)

    def test_rerun_does_not_append_and_mart_reconciles(self):
        clean, rejected, _ = transform(self.frame())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = load(clean, rejected, root)
            content = (root / 'data/processed/mart_invoice.csv').read_bytes()
            self.assertEqual(first, load(clean, rejected, root))
            self.assertEqual(content, (root / 'data/processed/mart_invoice.csv').read_bytes())
            self.assertEqual(first['mart_invoice'], 3)

    def test_conflicting_invoice_attributes_fail(self):
        frame = self.frame()
        frame.loc[1, 'Country'] = 'France'
        with self.assertRaisesRegex(ValueError, 'conflicting Country'):
            transform(frame)

    def test_schema_drift_fails(self):
        with self.assertRaisesRegex(ValueError, 'schema'):
            transform(self.frame().drop(columns=['Country']))


if __name__ == '__main__':
    unittest.main()
