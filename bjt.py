"""Engineering logic for the BJT common-emitter DC bias calculator.

Pure functions only: no Flask, no HTML, no I/O.
"""

import math
from dataclasses import dataclass
from typing import Mapping


FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

LABELS = {
    "vcc": "VCC (Supply Voltage)",
    "r1": "R1 (Upper Divider)",
    "r2": "R2 (Lower Divider)",
    "rc": "RC (Collector Resistor)",
    "re": "RE (Emitter Resistor)",
    "beta": "beta (Current Gain)",
    "vbe": "VBE (Base-Emitter Voltage)",
}

_RESISTORS = ("r1", "r2", "rc", "re")

VCE_SAT = 0.2

CUTOFF_WARNING = "Cutoff: ไบอัสฐาน-อิมิตเตอร์ไม่ forward (IB ≤ 0)"
SATURATION_WARNING = (
    "Saturation: VCE ที่คำนวณได้ ≤ VCE(sat) = 0.2 V "
    "โมเดลย่าน active ใช้ไม่ได้แล้ว"
)


def _symbol(field):
    return LABELS[field].split(" ", 1)[0]


def validate_inputs(raw: Mapping[str, str]):
    """Parse and validate raw form strings.

    Returns ``(values, errors)`` where ``values`` maps field names to floats
    and ``errors`` maps field names to Thai messages. An empty ``errors``
    dict means the input is valid.
    """
    values = {}
    errors = {}

    for field in FIELDS:
        text = (raw.get(field) or "").strip()
        try:
            value = float(text)
        except ValueError:
            errors[field] = f"{_symbol(field)} ต้องเป็นตัวเลข"
            continue
        if not math.isfinite(value):
            errors[field] = f"{_symbol(field)} ต้องเป็นตัวเลข"
            continue
        values[field] = value

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "VCC ต้องมากกว่า 0 V"

    for field in _RESISTORS:
        if field in values and values[field] <= 0:
            errors[field] = f"{_symbol(field)} ต้องมากกว่า 0 โอห์ม"

    if "beta" in values and values["beta"] < 1:
        errors["beta"] = "beta ต้องมีค่าอย่างน้อย 1"

    if "vbe" in values and "vcc" in values:
        if values["vbe"] < 0 or values["vbe"] >= values["vcc"]:
            errors["vbe"] = "VBE ต้องอยู่ระหว่าง 0 V กับ VCC"

    return values, errors


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


def classify_region(ib_a: float, vce_v: float) -> str:
    if ib_a <= 0:
        return "cutoff"
    if vce_v <= VCE_SAT:
        return "saturation"
    return "active"


def _cutoff_point(vcc: float, vbb: float) -> OperatingPoint:
    return OperatingPoint(0.0, 0.0, 0.0, vbb, vcc, 0.0, vcc)


def analyze_ce_bias(*, vcc, r1, r2, rc, re, beta, vbe) -> BiasResult:
    """Voltage-divider bias analysed with the textbook Thevenin method."""
    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)

    if vbb <= vbe:
        return BiasResult(_cutoff_point(vcc, vbb), "cutoff", (CUTOFF_WARNING,))

    ib = (vbb - vbe) / (rb + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    vb = vbb - ib * rb
    vc = vcc - ic * rc
    ve = ie * re
    vce = vc - ve

    region = classify_region(ib, vce)
    warnings = (SATURATION_WARNING,) if region == "saturation" else ()
    point = OperatingPoint(ib, ic, ie, vb, vc, ve, vce)
    return BiasResult(point, region, warnings)


CHECK_TOLERANCE = 1e-6


def _solve_linear_system(a, b):
    """Gaussian elimination with partial pivoting; returns the solution."""
    n = len(b)
    a = [row[:] for row in a]
    b = b[:]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-15:
            raise ValueError("singular system")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            b[col], b[pivot] = b[pivot], b[col]
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for k in range(col, n):
                a[row][k] -= factor * a[col][k]
            b[row] -= factor * b[col]

    x = [0.0] * n
    for row in range(n - 1, -1, -1):
        total = b[row] - sum(a[row][k] * x[k] for k in range(row + 1, n))
        x[row] = total / a[row][row]
    return x


def solve_nodal(*, vcc, r1, r2, rc, re, beta, vbe) -> OperatingPoint:
    """Independent check: solve the same circuit by nodal analysis.

    Unknowns are ``[VB, VC, VE, IB]``; the system is KCL at each node plus
    the base-emitter voltage-source constraint.
    """
    vbb = vcc * r2 / (r1 + r2)
    if vbb <= vbe:
        return _cutoff_point(vcc, vbb)

    a = [
        [1 / r1 + 1 / r2, 0.0, 0.0, 1.0],
        [0.0, 1 / rc, 0.0, beta],
        [0.0, 0.0, 1 / re, -(beta + 1)],
        [1.0, 0.0, -1.0, 0.0],
    ]
    b = [vcc / r1, vcc / rc, 0.0, vbe]

    vb, vc, ve, ib = _solve_linear_system(a, b)
    return OperatingPoint(ib, beta * ib, (beta + 1) * ib,
                          vb, vc, ve, vc - ve)


def compare_operating_points(a: OperatingPoint, b: OperatingPoint) -> float:
    """Largest relative difference across IB, IC and VCE."""
    worst = 0.0
    for x, y in ((a.ib_a, b.ib_a), (a.ic_a, b.ic_a), (a.vce_v, b.vce_v)):
        scale = max(abs(x), abs(y), 1e-12)
        worst = max(worst, abs(x - y) / scale)
    return worst
