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
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}

UNITS = {
    "vcc": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rc": "Ω",
    "re": "Ω",
    "beta": "–",
    "vbe": "V",
}

FIELDS = [(field, bjt.LABELS[field]) for field in bjt.FIELDS]


def _is_finite(point):
    return all(math.isfinite(value) for value in astuple(point))


def _render_error(form, message):
    return render_template("index.html", fields=FIELDS, form=form,
                           errors={"_form": message}, result=None,
                           units=UNITS, vce_sat=bjt.VCE_SAT), 400


@app.template_filter("current")
def format_current(amps):
    if amps == 0:
        return "0.000 A"
    if abs(amps) >= 1e-3:
        return f"{amps * 1e3:.3f} mA"
    if abs(amps) >= 1e-6:
        return f"{amps * 1e6:.3f} µA"
    return f"{amps:.3f} A"


@app.template_filter("voltage")
def format_voltage(volts):
    return f"{volts:.3f} V"


@app.get("/")
def index():
    return render_template("index.html", fields=FIELDS, form=DEFAULTS,
                           errors={}, result=None, units=UNITS,
                           vce_sat=bjt.VCE_SAT)


@app.post("/")
def calculate():
    form = {field: request.form.get(field, "") for field in bjt.FIELDS}
    values, errors = bjt.validate_inputs(form)

    if errors:
        return render_template("index.html", fields=FIELDS, form=form,
                               errors=errors, result=None, units=UNITS,
                               vce_sat=bjt.VCE_SAT), 400

    try:
        result = bjt.analyze_ce_bias(**values)
        independent = bjt.solve_nodal(**values)
    except (ValueError, ZeroDivisionError, OverflowError):
        return _render_error(
            form, "ผลลัพธ์เกินขอบเขตที่คำนวณได้ กรุณาลดขนาดค่าอินพุต")

    if not (_is_finite(result.point) and _is_finite(independent)):
        return _render_error(
            form, "ผลลัพธ์เกินขอบเขตที่คำนวณได้ กรุณาลดขนาดค่าอินพุต")

    difference = bjt.compare_operating_points(result.point, independent)

    return render_template(
        "index.html",
        fields=FIELDS,
        form=form,
        errors={},
        result=result,
        independent=independent,
        difference=difference,
        agrees=difference <= bjt.CHECK_TOLERANCE,
        units=UNITS,
        vce_sat=bjt.VCE_SAT,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
