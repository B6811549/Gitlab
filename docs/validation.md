# Lab 03 — Browser Acceptance Test Results (A1–A5)

วิธีตรวจหลัก: **OpenCode Browser** (Chromium ในแอป) เปิด `http://127.0.0.1:5002/`  
Playwright MCP: **NOT RUN** — เซสชันนี้ไม่มี MCP `playwright` เชื่อมอยู่ และคำสั่ง `opencode` ไม่ได้อยู่ใน PATH จึงตรวจรายการ MCP ผ่าน CLI ไม่ได้ (ทดแทนด้วย OpenCode Browser ตามที่ใบงานอนุญาต)

เงื่อนไขร่วม: V<sub>CC</sub> = 12 V, R<sub>C</sub> = 2.2 kΩ, β = 100, V<sub>BE</sub> = 0.70 V  
เกณฑ์: ΔI<sub>C</sub> ≤ 0.01 mA, ΔV<sub>CE</sub> ≤ 0.02 V เทียบกับค่าอ้างอิงที่คำนวณด้วยมือ (ไม่ปัดเศษ)

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ | หลักฐาน |
|------|----------------------|-----------------|----------|----------|--------|----------|
| A1 · โหมดเดิม | Divider · R<sub>1</sub> = 100 kΩ, R<sub>2</sub> = 22 kΩ, R<sub>E</sub> = 1 kΩ | ตรงกับ Lab 2 ก่อนแก้<br>I<sub>C</sub> = 1.23 mA · V<sub>CE</sub> = 8.05 V | V<sub>B</sub> 1.94 V · V<sub>E</sub> 1.24 V · V<sub>C</sub> 9.29 V<br>V<sub>CE</sub> **8.05 V** · I<sub>B</sub> 12.3 µA · I<sub>C</sub> **1.23 mA** · I<sub>E</sub> 1.24 mA | OpenCode Browser | ผ่าน (ΔI<sub>C</sub> = 0, ΔV<sub>CE</sub> = 0) | ผลตาราง DC Bias Results; ตรงกับ baseline HEAD `2f37fac` ที่วัดผ่าน HTTP |
| A2 · Fixed | Fixed · R<sub>B</sub> = 1 MΩ | คำนวณได้โดยไม่ต้องกรอก R<sub>E</sub><br>I<sub>C</sub> = 1.13 mA · V<sub>CE</sub> = 9.51 V | V<sub>B</sub> 0.70 V · V<sub>E</sub> 0.00 V · V<sub>C</sub> 9.51 V<br>V<sub>CE</sub> **9.51 V** · I<sub>B</sub> 11.3 µA · I<sub>C</sub> **1.13 mA** · I<sub>E</sub> 1.14 mA | OpenCode Browser | ผ่าน (ΔI<sub>C</sub> = 0, ΔV<sub>CE</sub> = 0) | `docs/evidence/a2-fixed.jpeg` (โหมด Fixed Bias, R<sub>B</sub> = 1000 kΩ, ไม่มีช่อง R<sub>E</sub>) |
| A3 · Emitter | Emitter · R<sub>B</sub> = 1 MΩ, R<sub>E</sub> = 1 kΩ | มีช่องและใช้ค่า R<sub>E</sub><br>I<sub>C</sub> = 1.03 mA · V<sub>CE</sub> = 8.71 V | V<sub>B</sub> 1.74 V · V<sub>E</sub> 1.04 V · V<sub>C</sub> 9.74 V<br>V<sub>CE</sub> **8.71 V** · I<sub>B</sub> 10.3 µA · I<sub>C</sub> **1.03 mA** · I<sub>E</sub> 1.04 mA | OpenCode Browser | ผ่าน (ΔI<sub>C</sub> < 0.01 mA, ΔV<sub>CE</sub> = 0) | ผลตาราง DC Bias Results (มีช่อง R<sub>E</sub> และใช้ค่าจริง) |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ R<sub>E</sub> = 2 kΩ | I<sub>C</sub> **ลดลง** จาก A3 (เพราะ R<sub>E</sub> มากขึ้น → I<sub>B</sub> ลด)<br>I<sub>C</sub> = 0.94 mA · V<sub>CE</sub> = 8.03 V | V<sub>B</sub> 2.60 V · V<sub>E</sub> 1.90 V · V<sub>C</sub> 9.93 V<br>V<sub>CE</sub> **8.03 V** · I<sub>B</sub> 9.4 µA · I<sub>C</sub> **940.1 µA (0.9401 mA)** · I<sub>E</sub> 949.5 µA | OpenCode Browser | ผ่าน (ΔI<sub>C</sub> = 0.0001 mA, ΔV<sub>CE</sub> = 0; I<sub>C</sub> ลดจาก A3) | ผลตาราง DC Bias Results |
| A5 · อินพุตผิด | Fixed · R<sub>B</sub> = 0 | มีข้อความให้แก้ R<sub>B</sub> เว็บไม่ล่ม ไม่แสดงผลเดิมเป็นผลรอบนี้ | HTTP **400** · ข้อความ **"RB ต้องมากกว่า 0 โอห์ม"** · ไม่มีตาราง DC Bias Results · ฟอร์มยังเป็นโหมด Fixed Bias | OpenCode Browser | ผ่าน | `docs/evidence/a5-error.jpeg` |

## ขั้นตอนตรวจทีละชั้น

1. **Flask พร้อม** — รัน `.\.venv\Scripts\python -m flask --app app run --port 5002` (ใช้ 5002 เพราะพอร์ต 5000 ถูก Flask ตัวอื่นยึดอยู่) แล้วเปิด `http://127.0.0.1:5002/` ได้ HTTP 200 และฟอร์ม Divider พร้อมผล A1
2. **MCP เชื่อม** — Playwright MCP **NOT RUN**: ไม่มี MCP `playwright` ในเซสชันนี้ และ `opencode mcp list` ใช้ไม่ได้เพราะไม่พบคำสั่ง `opencode`
3. **เอเจนต์ใช้ Browser ได้** — เปิดหน้าเว็บด้วย OpenCode Browser, อ่าน snapshot และ `evaluate` เห็น `bias_mode`, `vcc`, `rc`, `beta`, `vbe` พร้อมใช้งาน (พบและแก้บั๊ก JS ที่ซ่อนทุกช่องก่อนรัน A1–A5 — commit `00e6ed4`)
4. **A1–A5** — กรอกฟอร์มจริงแล้ว submit ผ่านเบราว์เซอร์ ผลตามตารางด้านบน

## ค่าอ้างอิงอิสระ (คำนวณด้วยมือ / เครื่องคิดเลข)

**สมการที่ใช้:**
- Fixed: I<sub>B</sub> = (V<sub>CC</sub> − V<sub>BE</sub>) / R<sub>B</sub> · V<sub>E</sub> = 0 · V<sub>B</sub> = V<sub>BE</sub> · V<sub>C</sub> = V<sub>CC</sub> − I<sub>C</sub>R<sub>C</sub> · V<sub>CE</sub> = V<sub>C</sub> − V<sub>E</sub>
- Emitter: I<sub>B</sub> = (V<sub>CC</sub> − V<sub>BE</sub>) / [R<sub>B</sub> + (β + 1)R<sub>E</sub>] · V<sub>E</sub> = I<sub>E</sub>R<sub>E</sub> · V<sub>B</sub> = V<sub>E</sub> + V<sub>BE</sub> · V<sub>C</sub> = V<sub>CC</sub> − I<sub>C</sub>R<sub>C</sub> · V<sub>CE</sub> = V<sub>C</sub> − V<sub>E</sub>
- ทุกโหมด: I<sub>C</sub> = βI<sub>B</sub> · I<sub>E</sub> = (β + 1)I<sub>B</sub>

**ตัวอย่างการคำนวณ A2 (Fixed, R<sub>B</sub> = 1 MΩ):**
- I<sub>B</sub> = (12 − 0.70) / 1,000,000 = 11.3 µA
- I<sub>C</sub> = 100 × 11.3 µA = 1.13 mA
- V<sub>C</sub> = 12 − (1.13 mA)(2.2 kΩ) = 9.514 V
- V<sub>CE</sub> = 9.514 − 0 = **9.51 V**

**ตัวอย่างการคำนวณ A3 (Emitter, R<sub>B</sub> = 1 MΩ, R<sub>E</sub> = 1 kΩ):**
- I<sub>B</sub> = 11.3 / (1,000,000 + 101 × 1,000) = 10.26 µA
- I<sub>C</sub> = 100 × 10.26 µA = 1.026 mA ≈ **1.03 mA**
- V<sub>E</sub> = (1.026 mA)(1.01) × 1 kΩ ≈ 1.04 V
- V<sub>C</sub> = 12 − (1.026 mA)(2.2 kΩ) ≈ 9.74 V
- V<sub>CE</sub> = 9.74 − 1.04 ≈ **8.71 V**

## บันทึกเพิ่มเติม

- ส่วนที่ AI ช่วยสร้าง: ฟังก์ชัน `analyze_fixed_bias()` และ `analyze_emitter_bias()` ใน `bjt.py`, การเลือกโหมดใน `app.py`, การปรับเทมเพลต `templates/index.html`
- ส่วนนักศึกษาตรวจเอง: ค่าอ้างอิงในตารางด้านบน (คำนวณด้วยมือ ไม่ได้ดึงจากโค้ด), การทวนผลผ่านเบราว์เซอร์, การระบุวิธีตรวจ (Playwright MCP / OpenCode Browser / Manual)
- โค้ดเลือกฟังก์ชันและแปลงหน่วยอยู่ที่ `app.py` (ฟังก์ชัน `_render_page`, `_apply_units`, `_mode_fields`)
- โหมด Divider (เก่า) ยังคงผลเดิม: A1 ได้ I<sub>C</sub> = 1.23 mA, V<sub>CE</sub> = 8.05 V เท่ากับ baseline HEAD `2f37fac`
- เทสต์เดิมทั้งหมด **40 ตัวผ่าน** (`.\.venv\Scripts\python -m pytest -q` → `40 passed`) และไม่ได้แก้ไฟล์เทสต์
