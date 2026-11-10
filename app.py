"""Flask routes for the BJT common-emitter DC bias calculator.

This module only parses the form, calls the engineering functions in
``bjt``, and renders the page.
"""

from flask import Flask, render_template, request

import bjt


app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "470",
    "beta": "150",
    "vbe": "0.7",
}

FIELDS = [(field, bjt.LABELS[field]) for field in bjt.FIELDS]


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
                           errors={}, result=None)


@app.post("/")
def calculate():
    form = {field: request.form.get(field, "") for field in bjt.FIELDS}
    values, errors = bjt.validate_inputs(form)

    if errors:
        return render_template("index.html", fields=FIELDS, form=form,
                               errors=errors, result=None), 400

    result = bjt.analyze_ce_bias(**values)
    independent = bjt.solve_nodal(**values)
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
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
