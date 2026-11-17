1. สาขาไฟฟ้าและอิเล็กทรอนิกส์ (วิศวกรรม/อาชีวศึกษา)
DC Circuit Calculator (เครื่องคำนวณวงจรไฟฟ้ากระแสตรง)

คำอธิบาย: โปรแกรมช่วยคำนวณและวิเคราะห์ค่ากระแสไฟฟ้า (Current) แรงดันไฟฟ้า และกำลังไฟฟ้า (Power) ในวงจรตัวต้านทานแบบอนุกรม ขนาน และผสม โดยออกแบบอินเทอร์เฟซให้ใช้งานง่าย ช่วยลดความผิดพลาดในการคำนวณทฤษฎีพื้นฐานของโอห์ม (Ohm's Law) สำหรับนักเรียนและผู้ฝึกหัด

Smart Resistor Color Code & Power Analyzer

คำอธิบาย: เครื่องมือคำนวณค่าความต้านทานจาก แถบสี พร้อมคำนวณพิกัดกำลังไฟฟ้า (Wattage) และกระแสสูงสุดที่วงจรทนได้ ช่วยให้นักศึกษาประเมินการเลือกใช้ขนาดอุปกรณ์ตัวต้านทานได้อย่างถูกต้องก่อนประกอบวงจรจริง

2. สาขาคอมพิวเตอร์และเทคโนโลยีสารสนเทศ (IT / Software)
Resistor Network Simulator (โปรแกรมจำลองเครือข่ายตัวต้านทาน)

คำอธิบาย: เว็บแอปพลิเคชันสำหรับจำลองวงจรตัวต้านทานแบบ Interactive ที่ผู้ใช้สามารถลากวางอุปกรณ์และกำหนดค่าความต้านทานได้ตามต้องการ ระบบจะแสดงผลการคำนวณกระแสและกำลังไฟฟ้าในแต่ละสาขาของวงจรทันที เพื่อใช้เป็นสื่อการเรียนการสอน

Automated Ohm’s Law Solver

คำอธิบาย: ซอฟต์แวร์ช่วยคำนวณค่าทางไฟฟ้าตามกฎของโอห์มแบบอัตโนมัติ เพียงป้อนค่าตัวแปรอย่างน้อย 2 ค่า (เช่น แรงดันและความต้านทาน) ระบบจะวิเคราะห์และคำนวณค่ากระแสไฟฟ้า พร้อมแสดงกราฟความสัมพันธ์ของกำลังไฟฟ้าเพื่อการเปรียบเทียบ

3. สาขาสื่อการเรียนรู้และเทคโนโลยีการศึกษา (Educational Technology)
Interactive Physics & Circuit Learning Toolkit

คำอธิบาย: ชุดสื่อการเรียนรู้ดิจิทัลเรื่องวงจรไฟฟ้าเบื้องต้น ประกอบด้วยเครื่องมือคำนวณกระแส กำลังไฟฟ้า และคำถามทบทวนความเข้าใจ ช่วยให้นักเรียนเห็นภาพการไหลของกระแสไฟฟ้าในวงจรตัวต้านทานได้ชัดเจนยิ่งขึ้น

## BJT Common-Emitter DC Bias (ENG29 2121)

เว็บแอป Flask หน้าเดียวสำหรับคำนวณจุดทำงานดีซีของวงจรไบอัส NPN common-emitter
รองรับ 3 โหมด โดยใช้สมการแยกกันใน `bjt.py` และเลือกฟังก์ชันด้วย `bias_mode`
ใน `app.py` (ไม่ fallback เป็น Divider เมื่อโหมดไม่รู้จัก — ตอบ HTTP 400)

| โหมด | ค่าที่กรอก | สมการหลัก |
|---|---|---|
| Voltage Divider Bias | V<sub>CC</sub>, R<sub>1</sub>, R<sub>2</sub>, R<sub>C</sub>, R<sub>E</sub>, β, V<sub>BE</sub> | V<sub>TH</sub> = V<sub>CC</sub>R<sub>2</sub>/(R<sub>1</sub>+R<sub>2</sub>), R<sub>TH</sub> = R<sub>1</sub>R<sub>2</sub>/(R<sub>1</sub>+R<sub>2</sub>), I<sub>B</sub> = (V<sub>TH</sub>−V<sub>BE</sub>)/(R<sub>TH</sub>+(β+1)R<sub>E</sub>) |
| Fixed Bias | V<sub>CC</sub>, R<sub>B</sub>, R<sub>C</sub>, β, V<sub>BE</sub> | I<sub>B</sub> = (V<sub>CC</sub>−V<sub>BE</sub>)/R<sub>B</sub>, V<sub>E</sub> = 0, V<sub>B</sub> = V<sub>BE</sub> |
| Emitter Bias | V<sub>CC</sub>, R<sub>B</sub>, R<sub>C</sub>, R<sub>E</sub>, β, V<sub>BE</sub> | I<sub>B</sub> = (V<sub>CC</sub>−V<sub>BE</sub>)/(R<sub>B</sub>+(β+1)R<sub>E</sub>), V<sub>E</sub> = I<sub>E</sub>R<sub>E</sub>, V<sub>B</sub> = V<sub>E</sub>+V<sub>BE</sub> |

ทุกโหมด: I<sub>C</sub> = βI<sub>B</sub>, I<sub>E</sub> = (β+1)I<sub>B</sub>,
V<sub>C</sub> = V<sub>CC</sub> − I<sub>C</sub>R<sub>C</sub>, V<sub>CE</sub> = V<sub>C</sub> − V<sub>E</sub>
และเตือน (ไม่ error) เมื่อ I<sub>B</sub> ≤ 0 หรือ V<sub>CE</sub> ≤ 0.2 V

- อินพุต: โหมดไบอัส + ค่าตามตาราง พร้อมเลือกหน่วย kΩ/MΩ
- เอาต์พุต: I<sub>B</sub>, I<sub>C</sub>, I<sub>E</sub>, V<sub>B</sub>, V<sub>C</sub>, V<sub>E</sub>, V<sub>CE</sub> พร้อมหน่วย และผลต่างระหว่างสูตรตำรากับ nodal analysis
- เอกสารผลตรวจ A1–A5 พร้อมภาพหลักฐาน: [`docs/validation.md`](docs/validation.md)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m flask --app app run --port 5000
```

เปิด `http://127.0.0.1:5000` แล้วเลือกโหมดและกด "Calculate DC Bias"
(หากพอร์ต 5000 ถูกใช้อยู่ ให้เปลี่ยนเลขพอร์ต เช่น `--port 5002`)

รันเทสทั้งหมด (เทสต์เดิม 40 ตัว ไม่มีการแก้ไฟล์เทสต์):

```powershell
.\.venv\Scripts\python -m pytest -q
```

### แหล่งโค้ดและความรับผิดชอบ

- GitHub: <https://github.com/B6811549/Gitlab>
- Commit โค้ดหลักของ Lab 03: `00e6ed4` (`fix: show active mode fields in the browser`)
- ส่วนที่ AI ช่วย: ร่างสูตรและฟังก์ชัน `analyze_fixed_bias()` / `analyze_emitter_bias()` ใน `bjt.py`, การเลือกโหมดและแปลงหน่วยใน `app.py`, ปรับ `templates/index.html` (ฟอร์ม, SVG ต่อวงจรตามโหมด, การซ่อน/แสดงช่อง)
- ส่วนที่นักศึกษาตรวจเอง: ค่าอ้างอิง A1–A5 คำนวณด้วยมือ, กรอกฟอร์มและอ่านผลผ่านเบราว์เซอร์จริง, ตรวจว่าโหมด Divider ให้ผลเดิม และโหมดไม่รู้จัก/อินพุตผิดแสดง error
