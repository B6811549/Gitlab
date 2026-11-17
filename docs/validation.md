# Lab 03 — Browser Acceptance Test Results (A1–A5)

วิธีตรวจ: **Playwright MCP** (หรือ OpenCode Browser / Manual — ระบุในตารางด้านล่าง)

เงื่อนไขร่วม: V<sub>CC</sub> = 12 V, R<sub>C</sub> = 2.2 kΩ, β = 100, V<sub>BE</sub> = 0.70 V  
เกณฑ์: ΔI<sub>C</sub> ≤ 0.01 mA, ΔV<sub>CE</sub> ≤ 0.02 V เทียบกับค่าอ้างอิงที่คำนวณด้วยมือ (ไม่ปัดเศษ)

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ | หลักฐาน |
|------|----------------------|-----------------|----------|----------|--------|----------|
| A1 · โหมดเดิม | Divider · R<sub>1</sub> = 100 kΩ, R<sub>2</sub> = 22 kΩ, R<sub>E</sub> = 1 kΩ | ตรงกับ Lab 2 ก่อนแก้<br>I<sub>C</sub> = 1.23 mA · V<sub>CE</sub> = 8.05 V | — | — | — | — |
| A2 · Fixed | Fixed · R<sub>B</sub> = 1 MΩ | คำนวณได้โดยไม่ต้องกรอก R<sub>E</sub><br>I<sub>C</sub> = 1.13 mA · V<sub>CE</sub> = 9.51 V | — | — | — | — |
| A3 · Emitter | Emitter · R<sub>B</sub> = 1 MΩ, R<sub>E</sub> = 1 kΩ | มีช่องและใช้ค่า R<sub>E</sub><br>I<sub>C</sub> = 1.03 mA · V<sub>CE</sub> = 8.71 V | — | — | — | — |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ R<sub>E</sub> = 2 kΩ | I<sub>C</sub> **ลดลง** จาก A3 (เพราะ R<sub>E</sub> มากขึ้น → I<sub>B</sub> ลด)<br>I<sub>C</sub> = 0.94 mA · V<sub>CE</sub> = 8.03 V | — | — | — | — |
| A5 · อินพุตผิด | Fixed · R<sub>B</sub> = 0 | มีข้อความให้แก้ R<sub>B</sub> เว็บไม่ล่ม ไม่แสดงผลเดิมเป็นผลรอบนี้ | — | — | — | — |

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
- โหมด Divider (เก่า) ยังคงผลเดิม: ทดสอบแล้วผ่านทั้ง 37 เทสเดิม
