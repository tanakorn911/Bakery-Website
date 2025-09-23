# Sweet Dreams Bakery Website 🍰

เว็บไซต์ร้านเบเกอรี่สมบูรณ์แบบที่ใช้ Flask, Bootstrap 5, และ SQLite พร้อมระบบจัดการสินค้า, ตะกร้าสินค้า, และระบบสมาชิก

## ✨ คุณสมบัติหลัก

- **🏠 หน้าหลัก**: แสดงสินค้าแนะนำและข้อมูลร้าน
- **📦 ระบบสินค้า**: จัดกลุ่มสินค้าตามหมวดหมู่ พร้อมการค้นหา
- **🛒 ตะกร้าสินค้า**: เพิ่ม/ลบ/แก้ไขสินค้า พร้อม AJAX
- **💳 ระบบสั่งซื้อ**: ฟอร์มสั่งซื้อที่ครบถ้วน
- **👥 ระบบสมาชิก**: สมัคร/เข้าสู่ระบบ
- **⚙️ หน้าแอดมิน**: จัดการสินค้าและข้อมูลร้าน
- **📱 Responsive Design**: ใช้ Bootstrap 5.0.2

## 🛠 เทคโนโลยี

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5.0.2, jQuery
- **Database**: SQLite3
- **Icons**: Font Awesome 6.4.0
- **Fonts**: Google Fonts (Prompt, Playfair Display)

## 📁 โครงสร้างโปรเจ็กต์

```
bakery-website/
│
├── app.py                      # แอปพลิเคชัน Flask หลัก
├── requirements.txt            # Python dependencies
├── bakery.db                  # ฐานข้อมูล SQLite (สร้างอัตโนมัติ)
├── README.md                  # คำแนะนำ
│
├── templates/                 # HTML Templates
│   ├── layout.html           # Base template
│   ├── index.html            # หน้าหลัก
│   ├── cart.html             # ตะกร้าสินค้า
│   ├── checkout.html         # ชำระเงิน
│   ├── login.html            # เข้าสู่ระบบ
│   ├── register.html         # สมัครสมาชิก
│   └── admin.html            # หน้าแอดมิน
│
├── static/                   # Static files
│   ├── css/
│   │   └── main.css         # CSS หลัก
│   ├── js/
│   │   └── main.js          # JavaScript หลัก
│   └── images/
│       ├── logo.png         # โลโก้ร้าน
│       └── products/        # รูปสินค้า
│           ├── chocolate_cake.jpg
│           ├── strawberry_cake.jpg
│           └── ...
```

## 🚀 การติดตั้ง

### 1. ติดตั้ง Python
ต้องมี Python 3.7+ บนเครื่อง

### 2. Clone โปรเจ็กต์
```bash
git clone <repository-url>
cd bakery-website
```

### 3. สร้าง Virtual Environment (แนะนำ)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 5. เตรียมโฟลเดอร์รูปภาพ
```bash
# สร้างโฟลเดอร์สำหรับรูปสินค้า
mkdir -p static/images/products

# เพิ่มรูปโลโก้และรูปสินค้า (ถ้ามี)
```

### 6. รันแอปพลิเคชัน
```bash
python app.py
```

เปิดเบราว์เซอร์ไปที่ `http://localhost:5000`

## 👤 บัญชีเริ่มต้น

### แอดมิน
- **Username**: `admin`
- **Password**: `admin123`
- **หน้าที่**: จัดการสินค้า, ดูสถิติ

### ลูกค้า
สร้างบัญชีใหม่ผ่านหน้าสมัครสมาชิก

## 📖 วิธีใช้งาน

### สำหรับลูกค้า
1. **เข้าชมเว็บไซต์**: ดูสินค้าในหน้าหลัก
2. **เลือกสินค้า**: คลิกเพื่อดูรายละเอียดและเพิ่มลงตะกร้า
3. **จัดการตะกร้า**: ปรับจำนวน/ลบสินค้าในตะกร้า
4. **สั่งซื้อ**: กรอกข้อมูลและชำระเงิน
5. **สมัครสมาชิก**: สร้างบัญชีเพื่อสะดวกในการสั่งซื้อ

### สำหรับแอดมิน
1. **เข้าสู่ระบบ**: ใช้บัญชี admin
2. **จัดการสินค้า**: เพิ่ม/แก้ไข/ลบสินค้า
3. **ดูสถิติ**: ยอดขาย, จำนวนสินค้า, ลูกค้า

## 🎨 การปรับแต่ง

### เปลี่ยนสี Theme
แก้ไขใน `static/css/main.css`:
```css
:root {
    --primary-color: #8B4513;      /* สีหลัก */
    --secondary-color: #d4af37;    /* สีรอง */
    --accent-color: #f4d03f;       /* สีเสริม */
}
```

### เพิ่มรูปสินค้า
1. วางรูปใน `static/images/products/`
2. ตั้งชื่อไฟล์ เช่น `new_product.jpg`
3. ในหน้าแอดมิน ใส่ชื่อไฟล์ในช่อง "ชื่อไฟล์รูปภาพ"

### เพิ่มหมวดหมู่ใหม่
แก้ไขฟังก์ชัน `seed_categories()` ใน `app.py`:
```python
categories = [
    ("หมวดใหม่", "New Category", "fas fa-icon", "คำอธิบาย", 6),
]
```

## 📚 API Endpoints

### สำหรับลูกค้า
- `GET /` - หน้าหลัก
- `GET /category/<id>` - สินค้าตามหมวดหมู่
- `POST /add_to_cart` - เพิ่มสินค้าลงตะกร้า
- `POST /update_cart` - อัปเดตจำนวนสินค้า
- `POST /remove_from_cart` - ลบสินค้าออกจากตะกร้า
- `GET /cart` - หน้าตะกร้าสินค้า
- `GET /checkout` - หน้าชำระเงิน
- `POST /checkout` - ส่งคำสั่งซื้อ

### Authentication
- `GET /login` - หน้าเข้าสู่ระบบ
- `POST /login` - ตรวจสอบการเข้าสู่ระบบ
- `GET /register` - หน้าสมัครสมาชิก
- `POST /register` - สร้างบัญชีใหม่
- `GET /logout` - ออกจากระบบ

### แอดมิน
- `GET /admin` - หน้าแอดมิน

## 🔧 การพัฒนาเพิ่มเติม

### เพิ่มฟีเจอร์ที่แนะนำ
- [ ] ระบบรีวิวและให้คะแนนสินค้า
- [ ] ระบบแจ้งเตือนสินค้าใหม่
- [ ] ระบบคูปองส่วนลด
- [ ] การชำระเงินผ่าน Payment Gateway
- [ ] ระบบติดตามสถานะคำสั่งซื้อ
- [ ] การอัปโหลดรูปผ่านเว็บ
- [ ] ระบบรายงานยอดขาย

### ฐานข้อมูล
สำหรับใช้งานจริงแนะนำให้เปลี่ยนจาก SQLite เป็น:
- PostgreSQL
- MySQL
- MongoDB

## 🐛 การแก้ไขปัญหา

### ปัญหาทั่วไป
1. **ไม่สามารถรันได้**: ตรวจสอบ Python version และ dependencies
2. **รูปไม่แสดง**: ตรวจสอบ path ใน `static/images/products/`
3. **ฐานข้อมูลผิดพลาด**: ลบไฟล์ `bakery.db` แล้วรันใหม่
4. **CSS ไม่เปลี่ยน**: ล้าง cache เบราว์เซอร์

### Debug Mode
เปิด Debug Mode ใน `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📝 การใช้งานเชิงพาณิชย์

เว็บไซต์นี้พร้อมใช้งานจริงสำหรับร้านเบเกอรี่ขนาดเล็ก-กลาง โดยควร:

1. **ตั้งค่า HTTPS**: ใช้ SSL Certificate
2. **ปรับ SECRET_KEY**: เปลี่ยนเป็นค่าที่ซับซ้อนกว่า
3. **ปรับแต่งฐานข้อมูล**: ใช้ฐานข้อมูลที่แข็งแรงกว่า SQLite
4. **เพิ่ม Monitoring**: ติดตามการใช้งานและข้อผิดพลาด
5. **สำรองข้อมูล**: ระบบ backup อัตโนมัติ

## 👥 การสนับสนุน

หากพบปัญหาหรือต้องการความช่วยเหลือ สามารถ:
- สร้าง Issue ใน GitHub
- ติดต่อผู้พัฒนา
- ดู Documentation เพิ่มเติม

## 📄 License

โปรเจ็กต์นี้อยู่ภายใต้ MIT License - ดูรายละเอียดใน LICENSE file

---

**พัฒนาโดย**: Sweet Dreams Development Team  
**เวอร์ชัน**: 1.0.0  
**อัปเดตล่าสุด**: 2024

Made with ❤️ for bakeries everywhere"# Bakery-Website" 
