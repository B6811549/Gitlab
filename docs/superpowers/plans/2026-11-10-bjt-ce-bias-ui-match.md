# Reference-Matching UI Plan — BJT DC Bias Web App

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the BJT bias page to match the supplied reference image pixel-for-pixel in structure, and accept the image's unit style (kΩ dropdowns) while keeping physically correct results.

**Architecture:** `bjt.py` stays pure numeric. `app.py` gains unit parsing (kΩ → Ω) and image-style number formatting. The Jinja template gains subscript labels, unit selects, a redrawn SVG schematic and a status banner. CSS is rewritten for the three-card lab look.

**Tech Stack:** Python 3.12, Flask 3.1, Jinja2, plain CSS, inline SVG, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Inputs stay exactly as the reference: VCC 12.0 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1.0 kΩ, β 100, VBE 0.70 V.
- Results are the physically correct values, not the image's (image is inconsistent: VB 2.20 V exceeds VBB 2.164 V).
- Thai validation/error sentences are preserved; visible labels follow the English reference.
- No new dependencies.
- Existing behavior kept: HTTP 400 on invalid input, finiteness guard, nodal cross-check, cutoff/saturation warnings.

## Review Focus

- A user switches a resistor from kΩ to Ω and back; the computed point must equal the same physical resistance.
- A user leaves a unit select unset (older form posts); resistors must default to Ω.
- A user types a non-numeric value with kΩ selected; the page must return 400 with a Thai message, not a traceback.
- Extreme finite values must still render finite values or the Thai "เกินขอบเขต" banner.
- The first GET must look like the reference screenshot without clicking.

---

### Task 1: Unit-aware parsing and reference number formatting

**Files:**
- Modify: `app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Produces: `UNIT_OPTIONS: dict[str, tuple[str, ...]]`, `DEFAULT_UNITS: dict[str, str]`, `DEFAULTS` in display units, `_apply_units(form, units) -> dict[str, str]`, `format_current(amps) -> str`, `format_voltage(volts) -> str`.
- `_apply_units` multiplies resistor fields by 1000 when their unit is `"kΩ"`; unknown/missing units mean Ω; non-numeric text passes through unchanged so `validate_inputs` reports it.

- [ ] **Step 1: Write failing tests** — unit conversion equals physical value, missing unit defaults to Ω, 2-decimal volts, 1-decimal µA.
- [ ] **Step 2: Run** `.\.venv\Scripts\python -m pytest tests/test_app.py -q` — expect failures.
- [ ] **Step 3: Implement** `DEFAULTS = {"vcc": "12.0", "r1": "100", "r2": "22", "rc": "2.2", "re": "1.0", "beta": "100", "vbe": "0.70"}`, `DEFAULT_UNITS`, `UNIT_OPTIONS`, `_apply_units`, and formatting (`V` 2 dp, `mA` 2 dp, `µA` 1 dp, zero → `0.0 µA`).
- [ ] **Step 4: Run** the test file — expect pass.
- [ ] **Step 5: Commit** `feat: parse resistor units and format like the reference`.

### Task 2: Reference markup (header, cards, unit selects, results, banner)

**Files:**
- Modify: `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `fields`, `form`, `units`, `unit_options`, `errors`, `result`, `independent`, `difference`, `agrees`, `vce_sat`.
- Produces: markup with header title `Lab 02: BJT DC Bias Web App`, card headings `Input Parameters`, `Circuit: Common-Emitter Amplifier`, `DC Bias Results`, button `Calculate DC Bias`, one `<select>` per field, subscript symbols, and the green `Active region approximation OK` banner.

- [ ] **Step 1: Write failing tests** — GET contains the header, three headings, seven selects, `kΩ`, `Calculate DC Bias`; POST valid shows `Active region approximation OK` and the correct 2-dp values; GET renders results for defaults.
- [ ] **Step 2: Run** — expect failures.
- [ ] **Step 3: Implement the template** with inline SVG icons (chip, gear, circuit, chart, code, calculator, check), subscript labels, unit selects, the results table and the status banner. Keep the nodal cross-check as a slim footer card.
- [ ] **Step 4: Run** — expect pass.
- [ ] **Step 5: Commit** `feat: match reference page markup`.

### Task 3: Reference schematic

**Files:**
- Modify: `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `form`, `units`, `result`.
- Produces: SVG with `VCC = 12.0 V`, `R1`, `R2`, `RC`, `RE`, `Q1`, `NPN`, `(β = 100)`, ground symbols, node dots, and computed node probes.

- [ ] **Step 1: Write failing test** — SVG contains `VCC`, `RC`, `RE`, `Q1`, `NPN`, `β`, and the default raw labels `100`, `22`, `2.2`, `1.0`.
- [ ] **Step 2: Run** — expect failure.
- [ ] **Step 3: Redraw the SVG** in the reference geometry (VCC rail top, R1 left, RC right, Q1 centre, R2 left-bottom, RE right-bottom, grounds).
- [ ] **Step 4: Run** — expect pass.
- [ ] **Step 5: Commit** `feat: redraw reference circuit schematic`.

### Task 4: Reference stylesheet and visual verification

**Files:**
- Modify: `static/style.css`
- Test: visual check via browser screenshot.

- [ ] **Step 1: Rewrite the stylesheet** for the reference palette, header badge, teal card headings, bordered value boxes with unit selects, blue-label results table, green status banner, and responsive collapse.
- [ ] **Step 2: Run** the full suite `.\.venv\Scripts\python -m pytest -q` — expect all tests pass.
- [ ] **Step 3: Restart** the app and screenshot the default page; confirm it matches the reference structure.
- [ ] **Step 4: Commit** `style: match reference lab layout`.
