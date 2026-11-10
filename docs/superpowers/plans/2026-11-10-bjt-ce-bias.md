# BJT Common-Emitter DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A one-page Flask app that computes and cross-checks the DC operating point of a voltage-divider-biased NPN common-emitter stage.

**Architecture:** `bjt.py` holds pure engineering functions (validation, Thevenin analysis, independent nodal solve, region classification). `app.py` only parses the form, calls `bjt`, and renders. One Jinja template, one stylesheet, two test files.

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8.x, stdlib `dataclasses`/`math` only (no numpy).

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Python 3.12.7; dependencies only `Flask>=3.0,<4` and `pytest>=8.0,<9`.
- `git` is not on PATH. Always invoke it as
  `& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe'`.
- Units: volts, ohms, dimensionless beta. Currents display in A / µA / mA to 3 decimals; voltages in V to 3 decimals.
- UI text: field labels and region badges in English/symbols (`VCC`, `IB`, `ACTIVE`); error and warning sentences in Thai.
- Stateless single page. `POST /` re-renders the same page; no redirects, no database, no session.
- `VCE_SAT = 0.2` V and `CHECK_TOLERANCE = 1e-6` are module constants in `bjt.py`.
- Do not modify `electrical.py`, `test_electrical.py`, or the existing README project list; only append a new section.
- No AC, transient, schematic editor, FET, PNP, or plotting.

## Review Focus

These are the input classes most likely to break the app; each has a test in the task that owns the code.

1. **VBE at or just above VBB** — equality must be cutoff, and VBE just below VBB must stay active with a tiny positive IB. (Task 2)
2. **Deep saturation with negative VCE** — must warn and show the unclamped value, not crash or clamp. (Task 2)
3. **Huge beta or resistors (1e6, 1e9)** — results must stay finite; no overflow or division by zero. (Task 2)
4. **Empty, non-numeric, `nan`, or `inf` fields** — HTTP 400 with a Thai message and no traceback. (Tasks 1, 4)
5. **Primary and nodal methods drifting** — the comparison must report near-zero for agreeing inputs and a real number when they differ. (Task 3)

---

### Task 1: Environment and input validation

**Files:**
- Create: `requirements.txt`
- Create: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `bjt.FIELDS: tuple[str, ...]` = `("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
  - `bjt.LABELS: dict[str, str]` mapping each field to its display label
  - `bjt.validate_inputs(raw: Mapping[str, str]) -> tuple[dict[str, float], dict[str, str]]`
    (returns parsed values and field → message errors; empty error dict means valid)

- [ ] **Step 1: Commit the approved design doc**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "docs: add BJT CE bias design"
```

- [ ] **Step 2: Create `requirements.txt` and the virtual environment**

```text
Flask>=3.0,<4
pytest>=8.0,<9
```

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

- [ ] **Step 3: Write the failing validation tests**

`tests/test_bjt.py`:

```python
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
```

- [ ] **Step 4: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: collection error, `ModuleNotFoundError: No module named 'bjt'`.

- [ ] **Step 5: Implement `bjt.py` validation**

Signatures and exact strings (bodies are straightforward):

```python
FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
LABELS = {"vcc": "VCC (V)", "r1": "R1 (Ω)", "r2": "R2 (Ω)",
          "rc": "RC (Ω)", "re": "RE (Ω)", "beta": "beta (β)",
          "vbe": "VBE (V)"}

def validate_inputs(raw):
    """Return (values, errors). Parse every field first, then range-check."""
```

Rules, in this order: parse with `float()` after `strip()`; a missing key, empty
string, `ValueError`, or `math.isfinite` failure yields
`f"{symbol} ต้องเป็นตัวเลข"` where `symbol` is the label's first token
(`"VCC"`, `"R1"`, `"beta"`, ...). Then: `vcc <= 0` → `"VCC ต้องมากกว่า 0 V"`;
any resistor `<= 0` → `f"{symbol} ต้องมากกว่า 0 โอห์ม"`; `beta < 1` →
`"beta ต้องมีค่าอย่างน้อย 1"`; `vbe < 0 or vbe >= vcc` →
`"VBE ต้องอยู่ระหว่าง 0 V กับ VCC"`.

- [ ] **Step 6: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: 6 passed.

- [ ] **Step 7: Commit**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add bjt.py tests/test_bjt.py requirements.txt .gitignore
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: validate BJT bias inputs"
```

---

### Task 2: Primary Thevenin analysis and region rules

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `bjt.validate_inputs` (Task 1).
- Produces:
  - `bjt.OperatingPoint` — frozen dataclass with float fields
    `ib_a, ic_a, ie_a, vb_v, vc_v, ve_v, vce_v` (positional order exactly as listed)
  - `bjt.BiasResult` — frozen dataclass with `point: OperatingPoint`,
    `region: str` (`"active" | "cutoff" | "saturation"`), `warnings: tuple[str, ...]`
  - `bjt.VCE_SAT: float` = `0.2`
  - `bjt.classify_region(ib_a: float, vce_v: float) -> str`
  - `bjt.analyze_ce_bias(*, vcc, r1, r2, rc, re, beta, vbe) -> BiasResult`

- [ ] **Step 1: Write the failing analysis tests**

Append to `tests/test_bjt.py`:

```python
import math

from bjt import (VCE_SAT, analyze_ce_bias, classify_region)


class PrimaryAnalysisTest(unittest.TestCase):
    def test_known_active_point(self):
        r = analyze_ce_bias(vcc=12, r1=47000, r2=10000, rc=2200,
                            re=470, beta=150, vbe=0.7)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())
        self.assertAlmostEqual(r.point.ib_a, 1.773972e-5, places=9)
        self.assertAlmostEqual(r.point.ic_a, 2.660958e-3, places=9)
        self.assertAlmostEqual(r.point.ie_a, 2.678698e-3, places=9)
        self.assertAlmostEqual(r.point.vb_v, 1.958987, places=5)
        self.assertAlmostEqual(r.point.vc_v, 6.145892, places=5)
        self.assertAlmostEqual(r.point.ve_v, 1.258988, places=5)
        self.assertAlmostEqual(r.point.vce_v, 4.886904, places=5)

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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: `ImportError` for `analyze_ce_bias` / `classify_region`.

- [ ] **Step 3: Implement the dataclasses and Thevenin analysis**

In `bjt.py`:

```python
@dataclass(frozen=True)
class OperatingPoint:
    ib_a: float
    ic_a: float
    ie_a: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float

@dataclass(frozen=True)
class BiasResult:
    point: OperatingPoint
    region: str
    warnings: tuple[str, ...]

VCE_SAT = 0.2

def classify_region(ib_a: float, vce_v: float) -> str: ...

def analyze_ce_bias(*, vcc, r1, r2, rc, re, beta, vbe) -> BiasResult: ...
```

`classify_region`: `ib_a <= 0` → `"cutoff"`; `vce_v <= VCE_SAT` → `"saturation"`;
else `"active"`.

`analyze_ce_bias`:
1. `vbb = vcc * r2 / (r1 + r2)`, `rb = r1 * r2 / (r1 + r2)`.
2. If `vbb <= vbe`: return cutoff `BiasResult(OperatingPoint(0, 0, 0, vbb, vcc, 0.0, vcc), "cutoff", ("Cutoff: ไบอัสฐาน-อิมิตเตอร์ไม่ forward (IB ≤ 0)",))`.
3. Otherwise `ib = (vbb - vbe) / (rb + (beta + 1) * re)`, `ic = beta * ib`,
   `ie = (beta + 1) * ib`, `vb = vbb - ib * rb`, `vc = vcc - ic * rc`,
   `ve = ie * re`, `vce = vc - ve`.
4. Region via `classify_region`. Saturation warning text:
   `"Saturation: VCE ที่คำนวณได้ ≤ VCE(sat) = 0.2 V โมเดลย่าน active ใช้ไม่ได้แล้ว"`.
   Active → empty tuple.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add bjt.py tests/test_bjt.py
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: compute CE bias operating point"
```

---

### Task 3: Independent nodal solution and cross-check

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `bjt.OperatingPoint`, `bjt.analyze_ce_bias`, `bjt.VCE_SAT` (Task 2).
- Produces:
  - `bjt.solve_nodal(*, vcc, r1, r2, rc, re, beta, vbe) -> OperatingPoint`
  - `bjt.compare_operating_points(a: OperatingPoint, b: OperatingPoint) -> float`
    (largest relative difference across IB, IC, VCE; denominator `max(|x|, |y|, 1e-12)`)
  - `bjt.CHECK_TOLERANCE: float` = `1e-6`

- [ ] **Step 1: Write the failing cross-check tests**

Append to `tests/test_bjt.py`:

```python
from bjt import OperatingPoint, compare_operating_points, solve_nodal


class NodalCheckTest(unittest.TestCase):
    def test_nodal_matches_known_point(self):
        p = solve_nodal(vcc=12, r1=47000, r2=10000, rc=2200,
                        re=470, beta=150, vbe=0.7)
        self.assertAlmostEqual(p.ib_a, 1.773972e-5, places=12)
        self.assertAlmostEqual(p.vce_v, 4.886904, places=9)

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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: `ImportError` for `solve_nodal` / `compare_operating_points`.

- [ ] **Step 3: Implement the nodal solver**

`bjt.py`, unknowns `[VB, VC, VE, IB]`:

```python
def _solve_linear_system(a, b):
    """Gaussian elimination with partial pivoting; returns the solution vector."""
```

Build `a` (4×4) and `b` (4×1) from KCL:

```
[1/r1 + 1/r2, 0,          0,          1        ] [VB]   [vcc/r1]
[0,           1/rc,       0,          beta     ] [VC] = [vcc/rc]
[0,           0,          1/re,       -(beta+1)] [VE]   [0     ]
[1,           0,         -1,          0        ] [IB]   [vbe   ]
```

If `vbb <= vbe` return the same cutoff `OperatingPoint` as Task 2
(`(0, 0, 0, vbb, vcc, 0.0, vcc)`) before solving. Otherwise return
`OperatingPoint(ib, beta*ib, (beta+1)*ib, vb, vc, ve, vc-ve)` from the solution.

`compare_operating_points` compares `ib_a`, `ic_a`, `vce_v` and returns the
maximum relative difference.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: 17 passed.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add bjt.py tests/test_bjt.py
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: cross-check bias with nodal analysis"
```

---

### Task 4: Flask page, routes, and formatting

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `bjt.FIELDS`, `bjt.LABELS`, `bjt.validate_inputs`, `bjt.analyze_ce_bias`,
  `bjt.solve_nodal`, `bjt.compare_operating_points`, `bjt.CHECK_TOLERANCE`.
- Produces:
  - `app.app` — Flask instance importable as `from app import app`
  - `GET /` and `POST /`; template context keys `fields`, `form`, `errors`,
    `result`, `independent`, `difference`, `agrees`
  - Jinja filters `current` (A/µA/mA, 3 decimals) and `voltage` (V, 3 decimals)

- [ ] **Step 1: Write the failing Flask tests**

`tests/test_app.py`:

```python
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
        self.assertIn("VCC", text)
        self.assertIn("คำนวณ", text)

    def test_post_valid_shows_point_and_cross_check(self):
        resp = self.client.post("/", data=VALID)
        self.assertEqual(resp.status_code, 200)
        text = resp.get_data(as_text=True)
        self.assertIn("ACTIVE", text)
        self.assertIn("17.740 µA", text)
        self.assertIn("2.661 mA", text)
        self.assertIn("4.887 V", text)
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
        self.assertIn("0.000 A", text)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py`**

```python
from flask import Flask, render_template, request
import bjt

app = Flask(__name__)
DEFAULTS = {"vcc": "12", "r1": "47000", "r2": "10000",
            "rc": "2200", "re": "470", "beta": "150", "vbe": "0.7"}
FIELDS = [(f, bjt.LABELS[f]) for f in bjt.FIELDS]

@app.template_filter("current")
def format_current(amps): ...   # 0 → "0.000 A"; >=1e-3 → mA; >=1e-6 → µA; else A

@app.template_filter("voltage")
def format_voltage(volts): ...  # f"{volts:.3f} V"

@app.get("/")
def index(): ...

@app.post("/")
def calculate(): ...
```

`index` renders with `form=DEFAULTS`, `errors={}`, `result=None`.
`calculate` reads `{f: request.form.get(f, "") for f in bjt.FIELDS}`; on errors
renders with that raw form, `errors`, and status 400; otherwise renders with
`result`, `independent`, `difference=compare_operating_points(...)`, and
`agrees=difference <= bjt.CHECK_TOLERANCE`.

Run block: `app.run(host="127.0.0.1", port=5000, debug=False)`.

- [ ] **Step 4: Implement `templates/index.html`**

Must include: `<html lang="th">`, the stylesheet link
`{{ url_for('static', filename='style.css') }}`, a `method="post"` form looping
`fields` with `name="{{ field }}"` and `value="{{ form.get(field, '') }}"`,
per-field error paragraphs, a submit button labelled `คำนวณ`, and when `result`
exists: a region badge `{{ result.region|upper }}`, each warning, a table of
`IB/IC/IE/VB/VC/VE/VCE` through the two filters, a heading
`ตรวจสอบข้ามวิธี (nodal solution อิสระ)`, the independent IB/IC/VCE values, and
`ผลต่างสูงสุด {{ '%.6f'|format(difference * 100) }}%` followed by
`ตรงกัน` when `agrees` else `ไม่ตรงกัน`.

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: 5 passed. (The stylesheet is created in Task 5.)

- [ ] **Step 6: Commit**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add app.py templates/index.html tests/test_app.py
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: add Flask page for CE bias"
```

---

### Task 5: Styling, README, demo, and push

**Files:**
- Create: `static/style.css`
- Modify: `README.md` (append a section; do not rewrite existing content)
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: the page from Task 4.
- Produces: a running demo at `http://127.0.0.1:5000` and a pushed `main`.

- [ ] **Step 1: Write the failing stylesheet tests**

Append to `tests/test_app.py`:

```python
    def test_stylesheet_served(self):
        resp = self.client.get("/static/style.css")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/css", resp.content_type)

    def test_page_links_stylesheet(self):
        text = self.client.get("/").get_data(as_text=True)
        self.assertIn("/static/style.css", text)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: 404 on `/static/style.css` and the link assertion fails.

- [ ] **Step 3: Implement `static/style.css`**

One stylesheet: readable max-width container, grid form, `.error` in red,
`.warning` with a tinted background, region badge colours for `.active`
(green), `.cutoff` (grey), `.saturation` (amber), and a two-column result
table. No external fonts or assets.

- [ ] **Step 4: Run the full test suite**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 24 passed (17 engineering + 7 Flask), none skipped.

- [ ] **Step 5: Append run instructions to `README.md`**

Append a `## BJT Common-Emitter DC Bias (ENG29 2121)` section with: what the
page computes, the input fields, and

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

then open `http://127.0.0.1:5000`, plus `.\.venv\Scripts\python -m pytest`.

- [ ] **Step 6: Verify the localhost demo**

```powershell
$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 2
(Invoke-WebRequest http://127.0.0.1:5000).StatusCode
Stop-Process -Id $proc.Id
```

Expected: `200`.

- [ ] **Step 7: Commit and push**

```powershell
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' add static/style.css README.md tests/test_app.py
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' commit -m "style: add bias calculator stylesheet and docs"
& 'C:\Users\B6811549\AppData\Local\Programs\Git\cmd\git.exe' push origin main
```

If push fails on credentials, stop and report the exact error; do not force.
