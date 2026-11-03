import unittest

from electrical import (
    analyze_dc,
    calculate_parallel_resistance,
    calculate_series_resistance,
)


class TestElectrical(unittest.TestCase):
    def test_dc_analysis(self):
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_series_resistance(self):
        self.assertAlmostEqual(calculate_series_resistance([2, 3, 6]), 11.0)

    def test_parallel_resistance(self):
        self.assertAlmostEqual(calculate_parallel_resistance([2, 3, 6]), 1.0)


if __name__ == "__main__":
    unittest.main()
