import unittest

from app import app

VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
         "re": "470", "beta": "150", "vbe": "0.7"}


class BiasPageTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_shows_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        text = resp.get_data(as_text=True)
        self.assertIn("Supply Voltage", text)
        self.assertIn("Calculate DC Bias", text)

    def test_post_valid_shows_point_and_cross_check(self):
        resp = self.client.post("/", data=VALID)
        self.assertEqual(resp.status_code, 200)
        text = resp.get_data(as_text=True)
        self.assertIn("ACTIVE", text)
        self.assertIn("17.7 µA", text)
        self.assertIn("2.66 mA", text)
        self.assertIn("4.89 V", text)
        self.assertIn("ตรวจสอบข้ามวิธี", text)
        self.assertIn("ตรงกัน", text)

    def test_post_invalid_returns_400(self):
        resp = self.client.post("/", data={**VALID, "vcc": "0"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("VCC ต้องมากกว่า 0 V", resp.get_data(as_text=True))

    def test_post_non_numeric_returns_400(self):
        resp = self.client.post("/", data={**VALID, "beta": "abc"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ต้องเป็นตัวเลข", resp.get_data(as_text=True))

    def test_cutoff_page(self):
        resp = self.client.post("/", data={**VALID, "r1": "20000", "r2": "1000"})
        self.assertEqual(resp.status_code, 200)
        text = resp.get_data(as_text=True)
        self.assertIn("CUTOFF", text)
        self.assertIn("0.0 µA", text)

    def test_stylesheet_served(self):
        resp = self.client.get("/static/style.css")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/css", resp.content_type)

    def test_page_links_stylesheet(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn("/static/style.css", text)

    def test_get_shows_three_panel_layout(self):
        text = self.client.get("/").get_data(as_text=True)
        for marker in ("Input Parameters", "Circuit", "DC Bias Results", "<svg"):
            self.assertIn(marker, text)

    def test_valid_result_shows_status_banner(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("transistor in active region", text)

    def test_saturation_page_shows_saturation_banner(self):
        data = {**VALID, "r1": "10000", "r2": "10000",
                "rc": "1000", "re": "100", "beta": "100"}
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("SATURATION", text)
        self.assertIn("transistor in saturation", text)

    def test_overflowing_input_returns_400_with_message(self):
        data = {**VALID, "beta": "1e308", "rc": "1e308", "re": "0.001"}
        resp = self.client.post("/", data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("เกินขอบเขต", resp.get_data(as_text=True))

    def test_extreme_resistors_render_finite_values(self):
        data = {**VALID, "r1": "1e308", "r2": "1e308"}
        resp = self.client.post("/", data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("nan", resp.get_data(as_text=True).lower())

    def test_kohm_units_match_physical_resistance(self):
        data = {"vcc": "12", "r1": "100", "r1_unit": "kΩ",
                "r2": "22", "r2_unit": "kΩ", "rc": "2.2", "rc_unit": "kΩ",
                "re": "1.0", "re_unit": "kΩ", "beta": "100", "vbe": "0.7"}
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("12.3 µA", text)
        self.assertIn("1.23 mA", text)
        self.assertIn("8.05 V", text)

    def test_missing_units_default_to_ohms(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("17.7 µA", text)

    def test_unknown_unit_falls_back_to_ohms(self):
        data = {**VALID, "r1_unit": "MΩ"}
        text = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("17.7 µA", text)

    def test_non_numeric_with_kohm_returns_400(self):
        data = {**VALID, "r1": "abc", "r1_unit": "kΩ"}
        resp = self.client.post("/", data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ต้องเป็นตัวเลข", resp.get_data(as_text=True))

    def test_voltage_uses_two_decimals(self):
        text = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("4.89 V", text)
        self.assertNotIn("4.887 V", text)
