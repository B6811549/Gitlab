import math
import unittest

from bjt import (FIELDS, VCE_SAT, OperatingPoint, analyze_ce_bias,
                 classify_region, compare_operating_points, solve_nodal,
                 validate_inputs)


def raw(**overrides):
    values = {"vcc": "12", "r1": "47000", "r2": "10000",
              "rc": "2200", "re": "470", "beta": "150", "vbe": "0.7"}
    values.update(overrides)
    return values


class ValidateInputsTest(unittest.TestCase):
    def test_accepts_valid_input(self):
        values, errors = validate_inputs(raw())
        self.assertEqual(errors, {})
        self.assertAlmostEqual(values["vcc"], 12.0)
        self.assertAlmostEqual(values["beta"], 150.0)

    def test_missing_or_non_numeric_field(self):
        for bad in ("", "abc", "inf", "nan"):
            _, errors = validate_inputs(raw(vcc=bad))
            self.assertIn("vcc", errors)
            self.assertIn("ต้องเป็นตัวเลข", errors["vcc"])

    def test_vcc_must_be_positive(self):
        _, errors = validate_inputs(raw(vcc="0"))
        self.assertEqual(errors["vcc"], "VCC ต้องมากกว่า 0 V")

    def test_resistors_must_be_positive(self):
        for field in ("r1", "r2", "rc", "re"):
            _, errors = validate_inputs(raw(**{field: "0"}))
            self.assertIn("ต้องมากกว่า 0 โอห์ม", errors[field])

    def test_beta_at_least_one(self):
        _, errors = validate_inputs(raw(beta="0.5"))
        self.assertEqual(errors["beta"], "beta ต้องมีค่าอย่างน้อย 1")

    def test_vbe_between_zero_and_vcc(self):
        for bad in ("-0.1", "12"):
            _, errors = validate_inputs(raw(vbe=bad))
            self.assertEqual(errors["vbe"], "VBE ต้องอยู่ระหว่าง 0 V กับ VCC")

class PrimaryAnalysisTest(unittest.TestCase):
    def test_known_active_point(self):
        r = analyze_ce_bias(vcc=12, r1=47000, r2=10000, rc=2200,
                            re=470, beta=150, vbe=0.7)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())
        self.assertAlmostEqual(r.point.ib_a, 1.77397243587898e-5, places=12)
        self.assertAlmostEqual(r.point.ic_a, 2.6609586538184696e-3, places=12)
        self.assertAlmostEqual(r.point.ie_a, 2.6786983781772597e-3, places=12)
        self.assertAlmostEqual(r.point.vb_v, 1.958988237743312, places=9)
        self.assertAlmostEqual(r.point.vc_v, 6.145890961599367, places=9)
        self.assertAlmostEqual(r.point.ve_v, 1.2589882377433121, places=9)
        self.assertAlmostEqual(r.point.vce_v, 4.886902723856055, places=9)

    def test_cutoff_when_base_not_forward_biased(self):
        r = analyze_ce_bias(vcc=12, r1=20000, r2=1000, rc=1000,
                            re=100, beta=100, vbe=0.7)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual((r.point.ib_a, r.point.ic_a, r.point.ie_a), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(r.point.vce_v, 12.0)
        self.assertAlmostEqual(r.point.vb_v, 12 * 1000 / 21000)
        self.assertEqual(len(r.warnings), 1)

    def test_cutoff_at_equality(self):
        r = analyze_ce_bias(vcc=10, r1=9000, r2=1000, rc=1000,
                            re=100, beta=100, vbe=1.0)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.point.ib_a, 0.0)

    def test_near_cutoff_stays_active(self):
        r = analyze_ce_bias(vcc=12, r1=47000, r2=10000, rc=2200,
                            re=470, beta=150, vbe=0.699)
        self.assertGreater(r.point.ib_a, 0.0)
        self.assertEqual(r.region, "active")

    def test_deep_saturation_warns_and_is_not_clamped(self):
        r = analyze_ce_bias(vcc=12, r1=10000, r2=10000, rc=1000,
                            re=100, beta=100, vbe=0.7)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.point.vce_v, 0.0)
        self.assertEqual(len(r.warnings), 1)

    def test_huge_beta_and_resistors_stay_finite(self):
        r = analyze_ce_bias(vcc=12, r1=1e9, r2=1e9, rc=1e3,
                            re=1e3, beta=1e6, vbe=0.7)
        self.assertTrue(math.isfinite(r.point.vce_v))

    def test_classify_region(self):
        self.assertEqual(classify_region(0.0, 12.0), "cutoff")
        self.assertEqual(classify_region(-1e-9, 12.0), "cutoff")
        self.assertEqual(classify_region(1e-3, VCE_SAT), "saturation")
        self.assertEqual(classify_region(1e-3, VCE_SAT + 0.01), "active")

class NodalCheckTest(unittest.TestCase):
    def test_nodal_matches_known_point(self):
        p = solve_nodal(vcc=12, r1=47000, r2=10000, rc=2200,
                        re=470, beta=150, vbe=0.7)
        self.assertAlmostEqual(p.ib_a, 1.77397243587898e-5, places=12)
        self.assertAlmostEqual(p.vce_v, 4.886902723856055, places=9)

    def test_methods_agree_across_grid(self):
        for vcc in (5, 12, 24):
            for beta in (50, 150, 400):
                for rc in (470, 2200, 10000):
                    kwargs = dict(vcc=vcc, r1=47000, r2=10000, rc=rc,
                                  re=470, beta=beta, vbe=0.7)
                    primary = analyze_ce_bias(**kwargs)
                    nodal = solve_nodal(**kwargs)
                    self.assertLess(
                        compare_operating_points(primary.point, nodal), 1e-6)

    def test_nodal_handles_cutoff(self):
        p = solve_nodal(vcc=12, r1=20000, r2=1000, rc=1000,
                        re=100, beta=100, vbe=0.7)
        self.assertEqual(p.ib_a, 0.0)
        self.assertAlmostEqual(p.vce_v, 12.0)

    def test_compare_reports_real_difference(self):
        a = OperatingPoint(1e-5, 2e-3, 2.01e-3, 2.0, 6.0, 1.0, 5.0)
        b = OperatingPoint(1e-5, 2.02e-3, 2.03e-3, 2.0, 6.0, 1.0, 5.0)
        self.assertAlmostEqual(compare_operating_points(a, b), 0.00990099, places=6)
