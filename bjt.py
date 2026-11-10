"""Engineering logic for the BJT common-emitter DC bias calculator.

Pure functions only: no Flask, no HTML, no I/O.
"""

import math
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
