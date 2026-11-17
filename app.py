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
    "rb": "1000",
    "beta": "100",
    "vbe": "0.70",
}

BIAS_MODES = (
    ("divider", "Voltage Divider Bias"),
    ("fixed", "Fixed Bias"),
    ("emitter", "Emitter Bias (single supply)"),
)

DEFAULT_BIAS_MODE = "divider"

FIELD_META = (
    {"name": "vcc", "symbol": "V<sub>CC</sub>",
     "caption": "Supply Voltage", "units": ("V",),
     "modes": ("divider", "fixed", "emitter")},
    {"name": "r1", "symbol": "R<sub>1</sub>",
     "caption": "Upper Divider", "units": ("Ω", "kΩ"),
     "modes": ("divider",)},
    {"name": "r2", "symbol": "R<sub>2</sub>",
     "caption": "Lower Divider", "units": ("Ω", "kΩ"),
     "modes": ("divider",)},
    {"name": "rc", "symbol": "R<sub>C</sub>",
     "caption": "Collector Resistor", "units": ("Ω", "kΩ"),
     "modes": ("divider", "fixed", "emitter")},
    {"name": "re", "symbol": "R<sub>E</sub>",
     "caption": "Emitter Resistor", "units": ("Ω", "kΩ"),
     "modes": ("divider", "emitter")},
    {"name": "rb", "symbol": "R<sub>B</sub>",
     "caption": "Base Resistor", "units": ("Ω", "kΩ", "MΩ"),
     "modes": ("fixed", "emitter")},
    {"name": "beta", "symbol": "β",
     "caption": "Current Gain", "units": ("–",),
     "modes": ("divider", "fixed", "emitter")},
    {"name": "vbe", "symbol": "V<sub>BE</sub>",
     "caption": "Base-Emitter Voltage", "units": ("V",),
     "modes": ("divider", "fixed", "emitter")},
)

UNIT_OPTIONS = {meta["name"]: meta["units"] for meta in FIELD_META}

DEFAULT_UNITS = {
    meta["name"]: ("kΩ" if "kΩ" in meta["units"] else meta["units"][0])
    for meta in FIELD_META
}

ALL_RESISTORS = ("r1", "r2", "rc", "re", "rb")

EXTREME_MESSAGE = "ผลลัพธ์เกินขอบเขตที่คำนวณได้ กรุณาลดขนาดค่าอินพุต"


def _mode_fields(bias_mode):
    """Return the tuple of field names required for the given bias mode."""
    return bjt.MODE_FIELDS.get(bias_mode, bjt.MODE_FIELDS["divider"])


def _read_units(source):
    """Pick the posted unit for each field.

    Missing or unknown units fall back to Ω when available so older or
    partial form posts keep their physical meaning.
    """
    units = {}
    for field in UNIT_OPTIONS:
        allowed = UNIT_OPTIONS[field]
        posted = source.get(f"{field}_unit")
        if posted in allowed:
            units[field] = posted
        elif "Ω" in allowed:
            units[field] = "Ω"
        else:
            units[field] = allowed[0]
    return units


def _apply_units(form, units, fields):
    """Convert the display-unit form strings to SI values as strings.

    kΩ and MΩ are multiplied by 1000 / 1e6. Missing or unknown units are
    treated as Ω. Non-numeric text passes through untouched so validation
    reports it. Only converts fields in ``fields``.
    """
    scaled = dict(form)
    for field in fields:
        text = (form.get(field) or "").strip()
        unit = units.get(field)
        if unit == "kΩ":
            try:
                scaled[field] = repr(float(text) * 1000)
            except ValueError:
                scaled[field] = text
        elif unit == "MΩ":
            try:
                scaled[field] = repr(float(text) * 1_000_000)
            except ValueError:
                scaled[field] = text
    return scaled


def _is_finite(point):
    return all(math.isfinite(value) for value in astuple(point))


def _page(form, units, errors, bias_mode, result=None, independent=None,
          difference=None, agrees=None):
    active_fields = set(_mode_fields(bias_mode))
    return render_template(
        "index.html",
        fields=FIELD_META,
        bias_modes=BIAS_MODES,
        bias_mode=bias_mode,
        active_fields=active_fields,
        form=form,
        units=units,
        errors=errors,
        result=result,
        independent=independent,
        difference=difference,
        agrees=agrees,
        vce_sat=bjt.VCE_SAT,
    )


def _unknown_mode_page():
    """Return the default Divider form with 400; never calculate a guess."""
    fields = _mode_fields(DEFAULT_BIAS_MODE)
    form = {k: DEFAULTS[k] for k in fields}
    units = {k: DEFAULT_UNITS[k] for k in fields}
    return _page(form, units, {"_form": "โหมดไบอัสไม่รู้จัก"},
                 DEFAULT_BIAS_MODE), 400


def _render_page(form, units, errors, bias_mode, values):
    if errors:
        return _page(form, units, errors, bias_mode), 400

    try:
        if bias_mode == "divider":
            result = bjt.analyze_ce_bias(**values)
            independent = bjt.solve_nodal(**values)
        elif bias_mode == "fixed":
            result = bjt.analyze_fixed_bias(**values)
            independent = None
        elif bias_mode == "emitter":
            result = bjt.analyze_emitter_bias(**values)
            independent = None
        else:
            return _page(form, units, {"_form": "โหมดไบอัสไม่รู้จัก"}, bias_mode), 400
    except (ValueError, ZeroDivisionError, OverflowError):
        return _page(form, units, {"_form": EXTREME_MESSAGE}, bias_mode), 400

    if not _is_finite(result.point):
        return _page(form, units, {"_form": EXTREME_MESSAGE}, bias_mode), 400

    difference = None
    agrees = None
    if independent is not None and _is_finite(independent):
        difference = bjt.compare_operating_points(result.point, independent)
        agrees = difference <= bjt.CHECK_TOLERANCE

    return _page(form, units, {}, bias_mode, result, independent,
                 difference, agrees)


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
    bias_mode = request.args.get("bias_mode", DEFAULT_BIAS_MODE)
    if bias_mode not in dict(BIAS_MODES):
        return _unknown_mode_page()
    fields = _mode_fields(bias_mode)
    defaults_subset = {k: DEFAULTS[k] for k in fields}
    units_subset = {k: DEFAULT_UNITS[k] for k in fields}
    values, errors = bjt.validate_inputs(
        _apply_units(defaults_subset, units_subset, fields), fields)
    return _render_page(defaults_subset, units_subset, errors, bias_mode, values)


@app.post("/")
def calculate():
    bias_mode = request.form.get("bias_mode", DEFAULT_BIAS_MODE)
    if bias_mode not in dict(BIAS_MODES):
        return _unknown_mode_page()
    fields = _mode_fields(bias_mode)
    form = {field: request.form.get(field, "") for field in fields}
    form["bias_mode"] = bias_mode
    units = _read_units(request.form)
    units_subset = {k: units[k] for k in fields if k in units}
    scaled = _apply_units(form, units_subset, fields)
    values, errors = bjt.validate_inputs(scaled, fields)
    return _render_page(form, units_subset, errors, bias_mode, values)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
