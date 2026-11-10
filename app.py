"""Flask routes for the BJT common-emitter DC bias calculator.

This module only parses the form, calls the engineering functions in
``bjt``, and renders the page.
"""

import math
from dataclasses import astuple

from flask import Flask, render_template, request

import bjt


app = Flask(__name__)

DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

FIELD_META = (
    {"name": "vcc", "symbol": "V<sub>CC</sub>",
     "caption": "Supply Voltage", "units": ("V",)},
    {"name": "r1", "symbol": "R<sub>1</sub>",
     "caption": "Upper Divider", "units": ("Ω", "kΩ")},
    {"name": "r2", "symbol": "R<sub>2</sub>",
     "caption": "Lower Divider", "units": ("Ω", "kΩ")},
    {"name": "rc", "symbol": "R<sub>C</sub>",
     "caption": "Collector Resistor", "units": ("Ω", "kΩ")},
    {"name": "re", "symbol": "R<sub>E</sub>",
     "caption": "Emitter Resistor", "units": ("Ω", "kΩ")},
    {"name": "beta", "symbol": "β",
     "caption": "Current Gain", "units": ("–",)},
    {"name": "vbe", "symbol": "V<sub>BE</sub>",
     "caption": "Base-Emitter Voltage", "units": ("V",)},
)

UNIT_OPTIONS = {meta["name"]: meta["units"] for meta in FIELD_META}

DEFAULT_UNITS = {
    meta["name"]: ("kΩ" if "kΩ" in meta["units"] else meta["units"][0])
    for meta in FIELD_META
}

RESISTORS = ("r1", "r2", "rc", "re")

EXTREME_MESSAGE = "ผลลัพธ์เกินขอบเขตที่คำนวณได้ กรุณาลดขนาดค่าอินพุต"


def _read_units(source):
    """Pick the posted unit for each field.

    Missing or unknown units fall back to Ω when available so older or
    partial form posts keep their physical meaning.
    """
    units = {}
    for field in bjt.FIELDS:
        allowed = UNIT_OPTIONS[field]
        posted = source.get(f"{field}_unit")
        if posted in allowed:
            units[field] = posted
        elif "Ω" in allowed:
            units[field] = "Ω"
        else:
            units[field] = allowed[0]
    return units


def _apply_units(form, units):
    """Convert the display-unit form strings to SI values as strings.

    kΩ is multiplied by 1000. Missing or unknown units are treated as Ω.
    Non-numeric text passes through untouched so validation reports it.
    """
    scaled = dict(form)
    for field in RESISTORS:
        text = (form.get(field) or "").strip()
        if units.get(field) == "kΩ":
            try:
                scaled[field] = repr(float(text) * 1000)
            except ValueError:
                scaled[field] = text
    return scaled


def _is_finite(point):
    return all(math.isfinite(value) for value in astuple(point))


def _page(form, units, errors, result=None, independent=None,
          difference=None, agrees=None):
    return render_template(
        "index.html",
        fields=FIELD_META,
        form=form,
        units=units,
        errors=errors,
        result=result,
        independent=independent,
        difference=difference,
        agrees=agrees,
        vce_sat=bjt.VCE_SAT,
    )


def _render_page(form, units, errors, values):
    if errors:
        return _page(form, units, errors), 400

    try:
        result = bjt.analyze_ce_bias(**values)
        independent = bjt.solve_nodal(**values)
    except (ValueError, ZeroDivisionError, OverflowError):
        return _page(form, units, {"_form": EXTREME_MESSAGE}), 400

    if not (_is_finite(result.point) and _is_finite(independent)):
        return _page(form, units, {"_form": EXTREME_MESSAGE}), 400

    difference = bjt.compare_operating_points(result.point, independent)
    return _page(form, units, {}, result, independent, difference,
                 difference <= bjt.CHECK_TOLERANCE)


@app.template_filter("current")
def format_current(amps):
    if abs(amps) >= 1e-3:
        return f"{amps * 1e3:.2f} mA"
    if abs(amps) >= 1e-6:
        return f"{amps * 1e6:.1f} µA"
    if amps == 0:
        return "0.0 µA"
    return f"{amps * 1e9:.1f} nA"


@app.template_filter("voltage")
def format_voltage(volts):
    return f"{volts:.2f} V"


@app.get("/")
def index():
    values, errors = bjt.validate_inputs(_apply_units(DEFAULTS, DEFAULT_UNITS))
    return _render_page(DEFAULTS, DEFAULT_UNITS, errors, values)


@app.post("/")
def calculate():
    form = {field: request.form.get(field, "") for field in bjt.FIELDS}
    units = _read_units(request.form)
    values, errors = bjt.validate_inputs(_apply_units(form, units))
    return _render_page(form, units, errors, values)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
