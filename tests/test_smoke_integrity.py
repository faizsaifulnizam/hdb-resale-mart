import unittest
from unittest.mock import patch
from tests import smoke_test

class SmokeChecks(unittest.TestCase):
    def test_nonfinite_town_fails_smoke(self):
        rows = smoke_test._load_csv(smoke_test.TOWN_CSV)
        for column in ('med_ppsm_2025q3','med_ppsm_2026q3','med_pct_change','rate_effect','mix_effect','interaction'):
            with self.subTest(column=column):
                bad = [dict(row) for row in rows]
                bad[2][column] = 'inf'
                with patch.object(smoke_test, '_load_csv', return_value=bad):
                    with self.assertRaises(AssertionError):
                        smoke_test.test_town_csv()

    def test_nonfinite_sensitivity_fails_smoke(self):
        rows = smoke_test._load_csv(smoke_test.SENS_CSV)
        for column in ('level_t0','total_delta','total_pct','rate','mix','interaction'):
            with self.subTest(column=column):
                bad = [dict(row) for row in rows]
                bad[2][column] = 'nan'
                with patch.object(smoke_test, '_load_csv', return_value=bad):
                    with self.assertRaises(AssertionError):
                        smoke_test.test_sensitivity_csv()
