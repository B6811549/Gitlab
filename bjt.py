"""Engineering logic for the BJT common-emitter DC bias calculator.

Pure functions only: no Flask, no HTML, no I/O.
"""

import math
from dataclasses import dataclass
from typing import Mapping


FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

LABELS = {
    "vcc": "VCC (V)",
    "r1": "R1 (Ω)",
    "r2": "R2 (Ω)",
    "rc": "RC (Ω)",
    "re": "RE (Ω)",
    "beta": "beta (β)",
    "vbe": "VBE (V)",
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
