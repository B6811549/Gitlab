# Lab 03 Bias Modes Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ปิดงาน Lab 03 บนโค้ดที่ต่อยอดจาก Lab 2 ให้เลือกได้สามโหมด (Divider / Fixed / Emitter) โดยผล Divider เดิมไม่เปลี่ยน และตรวจ A1–A5 ผ่าน Browser

**Architecture:** คง `bjt.py` เป็น pure functions และ `app.py` เป็นชั้นรับฟอร์ม/แปลงหน่วย/เลือกฟังก์ชัน เดิม dataclass ยังอยู่เพื่อให้เทสต์เดิมใช้ได้ และเพิ่ม `as_dict()` เป็นสัญญาผลลัพธ์ร่วมให้ Flask/template ใช้

**Tech Stack:** Python 3.12, Flask 3.1, Jinja2, pytest (เทสต์เดิมเท่านั้น), Playwright MCP หรือ OpenCode Browser

**Spec:** ใบงาน `ENG29_2121_Lab03_BJT_Bias_Web_App.html` (ไฟล์ที่ผู้ใช้แนบ) และ `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md` (Lab 2)

## Global Constraints

- ผล Divider ต้องคงเดิม: A1 ได้ IC = 1.23 mA, VCE = 8.05 V (baseline จาก HEAD `2f37fac` ผ่าน HTTP แล้ว)
- **ห้ามเพิ่ม/แก้ไฟล์ unittest** — ใช้ `tests/` เดิม 40 ตัวที่ต้องเขียวตลอด
- ไม่เพิ่ม dependency ใหม่
- แปลงหน่วยเฉพาะจุดรับฟอร์มใน `app._apply_units()`: kΩ ×1,000, MΩ ×1,000,000; `bjt.py` ใช้ Ω/A เท่านั้น
- ข้อความ error/warning ภาษาไทยคงเดิม
- โหมดไม่รู้จักต้องตอบ 400 ไม่คำนวณเป็น Divider
- ตรวจผลจริงผ่าน Browser ด้วยตาราง A1–A5 ของผู้ใช้ ไม่ใช้ค่าจากโค้ดเป็นค่าอ้างอิง

## Formulas (per mode)

- **Divider (existing, unchanged):** `VTH = VCC·R2/(R1+R2)`, `RTH = R1R2/(R1+R2)`, `IB = (VTH−VBE)/(RTH+(β+1)RE)`
- **Fixed:** `IB = (VCC−VBE)/RB`, `IC = βIB`, `IE = (β+1)IB`, `VE = 0`, `VB = VBE`, `VC = VCC−ICRC`, `VCE = VC−VE`
- **Emitter:** `IB = (VCC−VBE)/(RB+(β+1)RE)`, `IC = βIB`, `IE = (β+1)IB`, `VE = IERE`, `VB = VE+VBE`, `VC = VCC−ICRC`, `VCE = VC−VE`
- **ทุกโหมด:** `IC = βIB`, `IE = (β+1)IB`; เตือน (ไม่ error) เมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V`

## Review Focus

- ผู้ใช้กรอก RB = 1 MΩ หรือ 1000 kΩ แล้วต้องได้ 1.13 mA ไม่ใช่ 1130 mA
- ผู้ใช้ส่ง `bias_mode` ที่ไม่รู้จักแล้วต้องเห็น error ไม่ใช่ผล Divider
- ผู้ใช้สลับโหมดแล้วต้องได้ฟอร์มค่าเริ่มต้นของโหมดนั้น ไม่ใช่ 400/ช่องว่าง
- โหมด Divider ต้องเห็นขั้ว Base ต่อกับจุดกลาง R1/R2 ใน SVG
- โหมด Fixed ต้องเห็น Emitter ต่อลงกราวด์ และ Emitter ต้องไม่วาด RE ซ้ำ

---

### Task 1: แก้หน่วย RB และการตรวจอินพุตตามโหมด

**Files:**
- Modify: `app.py:80-96` (`_read_units`)
- Verify: `tests/` เดิม (ไม่แก้)

**Interfaces:**
- Consumes: `UNIT_OPTIONS: dict[str, tuple[str, ...]]`, `bjt.MODE_FIELDS`, `bjt.validate_inputs(raw, fields)`
- Produces: `_read_units(source) -> dict[str, str]` คืนหน่วยครบทุก 8 ช่อง รวม `rb`

- [ ] **Step 1: เปลี่ยนลูปใน `_read_units` จาก `for field in bjt.FIELDS` เป็น `for field in UNIT_OPTIONS`** เพื่อให้ `rb_unit` ถูกอ่าน (ไม่แก้ `bjt.FIELDS` เพราะเทสต์เดิมเรียก `validate_inputs()` แบบไม่มี `rb`)
- [ ] **Step 2: รันเทสต์เดิม**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: `40 passed`

- [ ] **Step 3: ตรวจ A2/A3/A5 ด้วย Flask test client (ไม่ใช่ไฟล์เทสต์)**

Run: `python -c` ยิง POST `bias_mode=fixed` ด้วย `rb=1000, rb_unit=kΩ` → ต้องได้ `IB 11.3 µA`, `IC 1.13 mA`, `VCE 9.51 V`
Run: POST `bias_mode=emitter` ด้วย `rb=1, rb_unit=MΩ`, `re=1, re_unit=kΩ` → `1.03 mA / 8.71 V`
Run: POST `bias_mode=fixed`, `rb=0` → HTTP 400 และข้อความ `RB ต้องมากกว่า 0 โอห์ม`

- [ ] **Step 4: Commit**

```powershell
git add app.py
git commit -m "fix: read rb unit and validate fixed/emitter inputs"
```

### Task 2: โหมดไม่รู้จักตอบ 400 และสลับโหมดด้วย GET

**Files:**
- Modify: `app.py:195-220` (`index`, `calculate`)
- Modify: `templates/index.html:67`

**Interfaces:**
- Consumes: `BIAS_MODES`, `DEFAULT_BIAS_MODE`, `_mode_fields`, `DEFAULTS`, `DEFAULT_UNITS`
- Produces: GET/POST ที่ `bias_mode` ไม่รู้จักคืน `400` พร้อม `_form = "โหมดไบอัสไม่รู้จัก"`; GET `/?bias_mode=fixed` คืนฟอร์ม Fixed พร้อมค่าเริ่มต้น

- [ ] **Step 1: ใน `calculate()` เลิก fallback** — ถ้า `bias_mode not in dict(BIAS_MODES)` ให้ render หน้าค่าเริ่มต้นของ Divider พร้อม error `_form` และคืน 400 (ไม่เรียกฟังก์ชันคำนวณ)
- [ ] **Step 2: ใน `index()` ทำแบบเดียวกันเมื่อ query `bias_mode` ไม่รู้จัก** (400 ไม่คำนวณ)
- [ ] **Step 3: เปลี่ยน select โหมดใน template** จาก `onchange="this.form.submit()"` เป็น `onchange="window.location='?bias_mode='+encodeURIComponent(this.value)"` เพื่อโหลดฟอร์มใหม่ด้วย GET; ปุ่ม Calculate ยัง POST เหมือนเดิม
- [ ] **Step 4: รันเทสต์เดิม**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: `40 passed`

- [ ] **Step 5: ตรวจด้วย HTTP**

Run: POST `bias_mode=nonsense` → `400` และมี `โหมดไบอัสไม่รู้จัก`
Run: GET `/?bias_mode=fixed` → `200`, มี `RB`, ค่าเริ่มต้น `1000 kΩ`
Run: GET `/?bias_mode=emitter` → `200`, มี `RB` และ `RE`

- [ ] **Step 6: Commit**

```powershell
git add app.py templates/index.html
git commit -m "fix: reject unknown bias mode and reload form via GET"
```

### Task 3: สัญญาผลลัพธ์ dict ร่วม (`as_dict`)

**Files:**
- Modify: `bjt.py` (เพิ่มหลัง `BiasResult`)
- Modify: `app.py:147-197` (`_render_page`, filters)
- Modify: `templates/index.html:260-297`

**Interfaces:**
- Produces:

```python
def as_dict(result: BiasResult, bias_mode: str) -> dict:
    return {
        "bias_mode": bias_mode,                  # str
        "ib_ma": ..., "ic_ma": ..., "ie_ma": ...,# mA (float)
        "vb_v": ..., "ve_v": ..., "vc_v": ..., "vce_v": ...,  # V (float)
        "region": result.region,                 # "active" | "cutoff" | "saturation"
        "warnings": list(result.warnings),       # list[str]
    }
```

- [ ] **Step 1: เพิ่ม `as_dict()` ใน `bjt.py`** แปลง A→mA ตอนสร้าง dict (dataclass และฟังก์ชันเดิมไม่เปลี่ยน)
- [ ] **Step 2: ใน `app._render_page` ส่ง `result=as_dict(result, bias_mode)` และเพิ่ม filter `current_ma(ma)` ที่เรียก `format_current(ma / 1000)`**
- [ ] **Step 3: เปลี่ยน template ให้อ่าน dict** — `result.vb_v|voltage`, `result.ib_ma|current_ma`, `result.region`, `result.vce_v`, `result.warnings`; คงบล็อก crosscheck ที่ใช้ `independent` dataclass เดิม
- [ ] **Step 4: รันเทสต์เดิม**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: `40 passed`

- [ ] **Step 5: ตรวจค่า A1–A4 ยังตรง** (test client หรือหน้าจริง): 1.23/8.05, 1.13/9.51, 1.03/8.71, 0.94/8.03

- [ ] **Step 6: Commit**

```powershell
git add bjt.py app.py templates/index.html
git commit -m "refactor: share dict result contract across bias modes"
```

### Task 4: แก้ SVG และการแสดงโหมด/ข้อผิดพลาด

**Files:**
- Modify: `templates/index.html:132-246` (SVG)
- Modify: `templates/index.html:103-105, 260-262`

**Interfaces:**
- Consumes: `bias_mode`, `form`, `units`, `errors`, `result`
- Produces: SVG ที่แต่ละโหมดต่อครบ; ข้อความ error ระบุโหมด; ไม่มีผลรอบเก่าค้างเมื่อ error

- [ ] **Step 1: แยกสาขา SVG ให้ชัด** — Divider: R1/R2/RC/RE + เส้น Base `110,235 → 163,235`; Fixed: RB/RC + Emitter `205,263 → 205,367` ลงกราวด์; Emitter: RB/RC/RE อย่างละครั้ง (ลบบล็อก RE ซ้ำและเงื่อนไข `{% if bias_mode == "emitter" %}{% else %}`)
- [ ] **Step 2: แสดงชื่อโหมดในกล่อง error** (`errors["_form"]`) โดยไม่ให้ตารางผลเดิมแสดงเมื่อมี error (`result` ต้องเป็น `None`)
- [ ] **Step 3: รันเทสต์เดิม**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: `40 passed`

- [ ] **Step 4: ตรวจ HTML ทั้งสามโหมด** — GET `/?bias_mode=divider|fixed|emitter` คืน `200`; Divider มี `R1`/`R2`, Fixed ไม่มี `R<sub>E</sub>` ใน SVG, Emitter มี `RE` ครั้งเดียว

- [ ] **Step 5: Commit**

```powershell
git add templates/index.html
git commit -m "fix: wire schematic per mode and label errors with mode"
```

### Task 5: ยืนยันทีละชั้น + A1–A5 + เอกสาร

**Files:**
- Modify: `docs/validation.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: ตาราง A1–A5 ของผู้ใช้; ค่าอ้างอิงใน `docs/validation.md`; `opencode.json`
- Produces: ตารางผลจริงครบ 5 กรณี + หลักฐาน + README ที่รันซ้ำได้

- [ ] **Step 1: ชั้นที่ 1 — Flask พร้อม**

Run: `.\.venv\Scripts\python -m flask --app app run` แล้วเปิด `http://127.0.0.1:5000/` ด้วยมือ
Expected: หน้า Divider พร้อมผล A1

- [ ] **Step 2: ชั้นที่ 2 — MCP เชื่อม**

Run: ตรวจรายการ MCP ใน OpenCode หรือ `opencode mcp list`
Expected: `playwright` แสดง connected (ถ้าไม่ ให้บันทึก NOT RUN และใช้ OpenCode Browser/Manual)

- [ ] **Step 3: ชั้นที่ 3 — เอเจนต์ใช้ Browser ได้**

Run: เปิด `http://127.0.0.1:5000/`, อ่าน snapshot
Expected: เห็นชื่อหน้าและช่อง `VCC`, `bias_mode`, `RB` อย่างน้อย 2 ช่อง พร้อมชื่อเครื่องมือที่ใช้

- [ ] **Step 4: รัน A1–A5 ตามตาราง**

| กรณี | อินพุต | คาดหมาย |
|---|---|---|
| A1 | Divider · R1 100 kΩ, R2 22 kΩ, RE 1 kΩ | IC 1.23 mA · VCE 8.05 V |
| A2 | Fixed · RB 1 MΩ | IC 1.13 mA · VCE 9.51 V |
| A3 | Emitter · RB 1 MΩ, RE 1 kΩ | IC 1.03 mA · VCE 8.71 V |
| A4 | Emitter · RE 2 kΩ | IC 0.94 mA (ลดจาก A3) · VCE 8.03 V |
| A5 | Fixed · RB 0 | 400 พร้อมข้อความให้แก้ RB |

- [ ] **Step 5: เติม `docs/validation.md`** — คอลัมน์เห็นจริง/วิธีตรวจ/สถานะ/หลักฐาน, แก้ "37 เทส" เป็น 40, บันทึก baseline A1 จาก HEAD
- [ ] **Step 6: อัปเดต `README.md`** — 3 โหมด, วิธีรัน, GitHub URL, Commit SHA ของ commit โค้ดหลัก, ส่วนที่ AI ช่วย
- [ ] **Step 7: ตรวจ diff และ commit**

```powershell
git diff
git diff --staged
git add docs/validation.md README.md
git commit -m "docs: record lab 03 browser acceptance and run steps"
```
