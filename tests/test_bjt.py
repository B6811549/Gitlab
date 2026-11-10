import unittest

from bjt import FIELDS, validate_inputs


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
