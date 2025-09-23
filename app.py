from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "sweetdreams_bakery_secret_2024"

DB_NAME = "bakery.db"

# ========================
# Database Functions
# ========================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """สร้างตารางฐานข้อมูล"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # ตารางผู้ใช้
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        phone TEXT,
        address TEXT,
        role TEXT DEFAULT 'customer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ตารางหมวดหมู่สินค้า
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        name_en TEXT,
        icon TEXT,
        description TEXT,
        display_order INTEGER DEFAULT 0
    )
    """)

    # ตารางสินค้า
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_en TEXT,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        image TEXT,
        category_id INTEGER,
        is_available INTEGER DEFAULT 1,
        is_featured INTEGER DEFAULT 0,
        stock_quantity INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)

    # ตารางคำสั่งซื้อ
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_amount DECIMAL(10,2) NOT NULL,
        status TEXT DEFAULT 'pending',
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_address TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # ตารางรายการสั่งซื้อ
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        total_price DECIMAL(10,2) NOT NULL,
        options TEXT,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    conn.commit()
    conn.close()


def seed_categories():
    """เพิ่มหมวดหมู่เริ่มต้น"""
    conn = get_db_connection()
    cursor = conn.cursor()

    categories = [
        ("เค้ก", "Cakes", "fas fa-birthday-cake", "เค้กสดใหม่ทุกรส", 1),
        ("ขนมปัง", "Pastries", "fas fa-bread-slice", "ขนมปังและเบเกอรี่", 2),
        ("เครื่องดื่ม", "Beverages", "fas fa-coffee", "กาแฟและเครื่องดื่ม", 3),
        ("ขนมหวาน", "Desserts", "fas fa-cookie-bite", "ขนมหวานและของหวาน", 4),
        ("เมนูพิเศษ", "Special", "fas fa-star", "เมนูพิเศษแนะนำ", 5)
    ]

    for name, name_en, icon, desc, order in categories:
        cursor.execute("""
            INSERT OR IGNORE INTO categories 
            (name, name_en, icon, description, display_order) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, name_en, icon, desc, order))

    conn.commit()
    conn.close()


def seed_products():
    """เพิ่มสินค้าตัวอย่าง"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # ดึง category_id
    cursor.execute("SELECT id, name FROM categories")
    categories_map = {name: id for id, name in cursor.fetchall()}

    products = [
        # เค้ก
        ("เค้กช็อกโกแลตดาร์ก", "Dark Chocolate Cake",
         "เค้กช็อกโกแลตเข้มข้น ทำจากโกโก้คุณภาพสูง เนื้อนุ่มชุ่มฉ่ำ",
         450.00, "chocolate_cake.jpg", categories_map.get("เค้ก"), 1, 1, 10),

        ("เค้กสตรอเบอร์รี่เฟรช", "Fresh Strawberry Cake",
         "เค้กสปันจ์นุ่ม ๆ หน้าสตรอเบอร์รี่สดใหม่ ครีมวิปปิ้งหวานมัน",
         520.00, "strawberry_cake.jpg", categories_map.get("เค้ก"), 1, 1, 8),

        ("เค้กวานิลลาคลาสสิก", "Classic Vanilla Cake",
         "เค้กวานิลลาสูตรดั้งเดิม หอมหวานนุ่มละมุน",
         380.00, "vanilla_cake.jpg", categories_map.get("เค้ก"), 1, 0, 12),

        # ขนมปัง
        ("ครัวซองต์เนย", "Butter Croissant",
         "ครัวซองต์กรอบนอกนุ่มใน ทำจากเนยฝรั่งเศสแท้ หอมหวานละมุน",
         85.00, "croissant.jpg", categories_map.get("ขนมปัง"), 1, 1, 20),

        ("ขนมปังโฮลวีท", "Whole Wheat Bread",
         "ขนมปังโฮลวีทเพื่อสุขภาพ นุ่มหอม อุดมไปด้วยเส้นใย",
         95.00, "whole_wheat.jpg", categories_map.get("ขนมปัง"), 1, 0, 15),

        ("เดนิชบลูเบอร์รี่", "Blueberry Danish",
         "เดนิชกรอบ ๆ ไส้บลูเบอร์รี่สดใหม่ หอมเนยและผลไม้",
         120.00, "blueberry_danish.jpg", categories_map.get("ขนมปัง"), 1, 1, 10),

        # เครื่องดื่ม
        ("กาแฟลาเต้พรีเมียม", "Premium Latte",
         "กาแฟเอสเปรสโซ่เข้มข้น ผสมนมสดคุณภาพสูง ลาเต้อาร์ตสวยงาม",
         120.00, "latte.jpg", categories_map.get("เครื่องดื่ม"), 1, 1, 50),

        ("คาปูชิโน่", "Cappuccino",
         "กาแฟคาปูชิโน่แบบดั้งเดิม ฟองนมนุ่ม หอมกาแฟเข้มข้น",
         110.00, "cappuccino.jpg", categories_map.get("เครื่องดื่ม"), 1, 0, 50),

        ("ชาเขียวมัทฉะลาเต้", "Matcha Green Tea Latte",
         "ชาเขียวมัทฉะเกรดพรีเมียม ผสมนมสด หอมหวานกำลังดี",
         140.00, "matcha_latte.jpg", categories_map.get("เครื่องดื่ม"), 1, 1, 30),

        # ขนมหวาน
        ("ทิรามิสุ", "Tiramisu",
         "ขนมหวานอิตาเลี่ยนแสนอร่อย เนื้อนุ่ม หอมกาแฟและมาสคาโปเน่",
         180.00, "tiramisu.jpg", categories_map.get("ขนมหวาน"), 1, 1, 12),

        ("พุดดิ้งคาราเมล", "Caramel Pudding",
         "พุดดิ้งเนียนนุ่ม ราดด้วยคาราเมลหอมหวาน",
         95.00, "caramel_pudding.jpg", categories_map.get("ขนมหวาน"), 1, 0, 20),

        ("เครปเค้กมะม่วง", "Mango Crepe Cake",
         "เครปบาง ๆ สลับชั้นครีม พร้อมมะม่วงสดใหม่",
         240.00, "mango_crepe.jpg", categories_map.get("ขนมหวาน"), 1, 1, 6)
    ]

    for product in products:
        cursor.execute("""
            INSERT OR IGNORE INTO products 
            (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, product)

    conn.commit()
    conn.close()


def create_admin_user():
    """สร้างผู้ใช้แอดมินเริ่มต้น"""
    conn = get_db_connection()
    cursor = conn.cursor()

    admin_password = generate_password_hash("admin123")
    cursor.execute("""
        INSERT OR IGNORE INTO users 
        (username, email, password, full_name, role) 
        VALUES (?, ?, ?, ?, ?)
    """, ("admin", "admin@sweetdreams.com", admin_password, "ผู้ดูแลระบบ", "admin"))

    conn.commit()
    conn.close()

# ========================
# Helper Functions
# ========================

def get_user_by_username(username):
    """ดึงข้อมูลผู้ใช้จาก username"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return user


def get_categories():
    """ดึงหมวดหมู่สินค้าทั้งหมด"""
    conn = get_db_connection()
    categories = conn.execute(
        "SELECT * FROM categories ORDER BY display_order"
    ).fetchall()
    conn.close()
    return categories


def get_products_by_category(category_id=None, featured_only=False):
    """ดึงสินค้าตามหมวดหมู่"""
    conn = get_db_connection()

    if category_id:
        if featured_only:
            products = conn.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE p.category_id = ? AND p.is_available = 1 AND p.is_featured = 1
                ORDER BY p.created_at DESC
            """, (category_id,)).fetchall()
        else:
            products = conn.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE p.category_id = ? AND p.is_available = 1
                ORDER BY p.created_at DESC
            """, (category_id,)).fetchall()
    else:
        if featured_only:
            products = conn.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE p.is_available = 1 AND p.is_featured = 1
                ORDER BY p.created_at DESC
            """).fetchall()
        else:
            products = conn.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE p.is_available = 1
                ORDER BY p.created_at DESC
            """).fetchall()

    conn.close()
    return products


def get_product_by_id(product_id):
    """ดึงสินค้าจาก ID"""
    conn = get_db_connection()
    product = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.id = ?
    """, (product_id,)).fetchone()
    conn.close()
    return product


def get_cart_total():
    """คำนวณยอดรวมในตะกร้า"""
    cart = session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values()) if cart else 0
    total_price = sum(item['price'] * item['quantity'] for item in cart.values()) if cart else 0
    return total_items, total_price

# ========================
# Context Processor - ส่งข้อมูลให้ทุก template
# ========================

@app.context_processor
def inject_global_data():
    """ส่งข้อมูลหมวดหมู่และจำนวนตะกร้าให้ทุกหน้า"""
    categories = get_categories()
    cart_total_items, _ = get_cart_total()

    return dict(
        categories=categories,
        cart_total_items=cart_total_items
    )

# ========================
# Routes - หน้าหลัก
# ========================

@app.route('/')
def index():
    """หน้าหลัก"""
    categories = get_categories()
    featured_products = get_products_by_category(featured_only=True)
    all_products = get_products_by_category()

    # จัดกลุ่มสินค้าตามหมวดหมู่
    products_by_category = {}
    for product in all_products:
        category_name = product['category_name']
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)

    return render_template('index.html', 
                         featured_products=featured_products,
                         products_by_category=products_by_category)

@app.route('/category/<int:category_id>')
def category_by_id(category_id):
    """หน้าหมวดหมู่สินค้าตาม ID"""
    categories = get_categories()
    products = get_products_by_category(category_id)

    # หาชื่อหมวดหมู่
    category_name = None
    for cat in categories:
        if cat['id'] == category_id:
            category_name = cat['name']
            break

    if not category_name:
        flash('ไม่พบหมวดหมู่ที่ต้องการ')
        return redirect(url_for('index'))

    return render_template('category.html',
                         products=products,
                         category_name=category_name)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # ให้ query คืนค่าเป็น dict-like object
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        return redirect(url_for('index'))

    return render_template("product_detail.html", product=product)

# ========================
# Authentication Routes
# ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """หน้าเข้าสู่ระบบ"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']

            flash(f'เข้าสู่ระบบสำเร็จ! ยินดีต้อนรับ {user["full_name"] or user["username"]}')
            return redirect(url_for('admin') if user['role'] == 'admin' else url_for('index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """หน้าสมัครสมาชิก"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        phone = request.form['phone']

        if password != confirm_password:
            flash('รหัสผ่านไม่ตรงกัน')
            return render_template('register.html')

        conn = get_db_connection()
        try:
            hashed_password = generate_password_hash(password)
            conn.execute("""
                INSERT INTO users (username, email, password, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, hashed_password, full_name, phone))
            conn.commit()
            flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('ชื่อผู้ใช้หรืออีเมลนี้มีอยู่แล้ว')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    """ออกจากระบบ"""
    session.clear()
    flash('ออกจากระบบเรียบร้อย')
    return redirect(url_for('index'))

# ========================
# Cart Management Routes
# ========================

@app.route('/cart')
def cart():
    """หน้าตะกร้าสินค้า"""
    cart_items = session.get('cart', {})
    total_items, total_price = get_cart_total()

    return render_template('cart.html',
                         cart_items=cart_items,
                         total_items=total_items,
                         total_price=total_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """เพิ่มสินค้าลงตะกร้า"""
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    options = data.get('options', '')

    product = get_product_by_id(int(product_id))
    if not product:
        return jsonify({'success': False, 'message': 'ไม่พบสินค้า'})

    cart = session.get('cart', {})
    cart_key = f"{product_id}_{options}" if options else product_id

    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
    else:
        cart[cart_key] = {
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': quantity,
            'options': options
        }

    session['cart'] = cart
    total_items, total_price = get_cart_total()

    return jsonify({
        'success': True,
        'message': f'เพิ่ม {product["name"]} ลงในตะกร้าแล้ว',
        'total_items': total_items,
        'total_price': total_price
    })

@app.route('/update_cart', methods=['POST'])
def update_cart():
    """อัปเดตจำนวนสินค้าในตะกร้า"""
    data = request.get_json()
    cart_key = data.get('cart_key')
    quantity = int(data.get('quantity', 1))

    cart = session.get('cart', {})
    if cart_key in cart:
        if quantity <= 0:
            del cart[cart_key]
        else:
            cart[cart_key]['quantity'] = quantity

    session['cart'] = cart
    total_items, total_price = get_cart_total()

    return jsonify({
        'success': True,
        'total_items': total_items,
        'total_price': total_price
    })

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """ลบสินค้าออกจากตะกร้า"""
    data = request.get_json()
    cart_key = data.get('cart_key')

    cart = session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]

    session['cart'] = cart
    total_items, total_price = get_cart_total()

    return jsonify({
        'success': True,
        'message': 'ลบสินค้าออกจากตะกร้าแล้ว',
        'total_items': total_items,
        'total_price': total_price
    })

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    """เคลียร์ตะกร้าทั้งหมด"""
    session['cart'] = {}
    return jsonify({
        'success': True,
        'message': 'เคลียร์ตะกร้าเรียบร้อยแล้ว',
        'total_items': 0,
        'total_price': 0
    })

# ========================
# Checkout Routes
# ========================

@app.route("/checkout", methods=["GET", "POST"]) 
def checkout():
    """หน้าชำระเงิน"""
    cart = session.get('cart', {})
    if not cart:
        flash('ตะกร้าสินค้าว่าง')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get form data
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        customer_address = request.form.get('customer_address', '')
        notes = request.form.get('notes', '')

        # Calculate totals
        total_items, total_price = get_cart_total()

        conn = get_db_connection()
        try:
            # Create order
            cursor = conn.execute("""
                INSERT INTO orders 
                (user_id, total_amount, customer_name, customer_phone, customer_address, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (session.get('user_id'), total_price, customer_name, customer_phone, customer_address, notes))

            order_id = cursor.lastrowid

            # Add order items
            for item in cart.values():
                conn.execute("""
                    INSERT INTO order_items 
                    (order_id, product_id, quantity, unit_price, total_price, options)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item['id'], item['quantity'], item['price'], 
                     item['price'] * item['quantity'], item.get('options', '')))

            conn.commit()

            # Clear cart
            session['cart'] = {}

            flash(f'ขอบคุณสำหรับคำสั่งซื้อ! หมายเลขคำสั่งซื้อ: #{order_id}')
            return redirect(url_for('order_detail', order_id=order_id))

        except Exception as e:
            conn.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}')
        finally:
            conn.close()

    # GET request - show checkout form
    total_items, total_price = get_cart_total()

    return render_template('checkout.html',
                         cart_items=cart,
                         total_items=total_items,
                         total_price=total_price)

# ========================
# User Profile Routes
# ========================

@app.route('/profile')
def profile():
    """หน้าโปรไฟล์ผู้ใช้"""
    if not session.get('user_id'):
        flash('กรุณาเข้าสู่ระบบก่อน')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session.get('user_id'),)
    ).fetchone()

    orders = conn.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (session.get('user_id'),)).fetchall()

    conn.close()

    return render_template('profile.html', user=user, orders=orders)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """อัปเดตโปรไฟล์ผู้ใช้"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    phone = request.form['phone']
    address = request.form['address']

    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE users SET full_name = ?, phone = ?, address = ?
            WHERE id = ?
        """, (full_name, phone, address, session.get('user_id')))
        conn.commit()
        session['full_name'] = full_name  # Update session data
        flash('อัปเดตข้อมูลเรียบร้อยแล้ว')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}')
    finally:
        conn.close()

    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    """เปลี่ยนรหัสผ่าน"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('รหัสผ่านใหม่ไม่ตรงกัน')
        return redirect(url_for('profile'))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT password FROM users WHERE id = ?", (session.get('user_id'),)
    ).fetchone()

    if not user or not check_password_hash(user['password'], current_password):
        flash('รหัสผ่านเดิมไม่ถูกต้อง')
        conn.close()
        return redirect(url_for('profile'))

    try:
        hashed_password = generate_password_hash(new_password)
        conn.execute("""
            UPDATE users SET password = ? WHERE id = ?
        """, (hashed_password, session.get('user_id')))
        conn.commit()
        flash('เปลี่ยนรหัสผ่านเรียบร้อยแล้ว')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}')
    finally:
        conn.close()

    return redirect(url_for('profile'))

# ========================
# Order Routes
# ========================

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """หน้ารายละเอียดคำสั่งซื้อ"""
    conn = get_db_connection()

    # Check permission
    if session.get('role') == 'admin':
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    elif session.get('user_id'):
        order = conn.execute("""
            SELECT * FROM orders 
            WHERE id = ? AND user_id = ?
        """, (order_id, session.get('user_id'))).fetchone()
    else:
        flash('กรุณาเข้าสู่ระบบก่อน')
        conn.close()
        return redirect(url_for('login'))

    if not order:
        flash('ไม่พบคำสั่งซื้อนี้')
        conn.close()
        return redirect(url_for('profile'))

    # Get order items
    order_items = conn.execute("""
        SELECT oi.*, p.name as product_name, p.image as product_image
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()

    conn.close()

    return render_template('order_detail.html', order=order, order_items=order_items)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    """ยกเลิกคำสั่งซื้อ"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'กรุณาเข้าสู่ระบบ'})

    conn = get_db_connection()

    # Check if order exists and belongs to user
    order = conn.execute("""
        SELECT * FROM orders 
        WHERE id = ? AND user_id = ? AND status = 'pending'
    """, (order_id, session.get('user_id'))).fetchone()

    if not order:
        conn.close()
        return jsonify({'success': False, 'message': 'ไม่พบคำสั่งซื้อหรือไม่สามารถยกเลิกได้'})

    try:
        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'ยกเลิกคำสั่งซื้อเรียบร้อยแล้ว'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/reorder/<int:order_id>', methods=['POST'])
def reorder(order_id):
    """สั่งซื้ออีกครั้ง"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'กรุณาเข้าสู่ระบบ'})

    conn = get_db_connection()

    # Get order items
    order_items = conn.execute("""
        SELECT oi.product_id, oi.quantity, oi.options, p.name, p.price, p.is_available
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.id = ? AND o.user_id = ?
    """, (order_id, session.get('user_id'))).fetchall()

    conn.close()

    if not order_items:
        return jsonify({'success': False, 'message': 'ไม่พบข้อมูลคำสั่งซื้อ'})

    # Add items to cart
    cart = session.get('cart', {})
    added_items = 0

    for item in order_items:
        if not item['is_available']:
            continue

        cart_key = f"{item['product_id']}_{item['options']}" if item['options'] else str(item['product_id'])

        cart[cart_key] = {
            'id': item['product_id'],
            'name': item['name'],
            'price': float(item['price']),
            'quantity': item['quantity'],
            'options': item['options'] or ''
        }
        added_items += 1

    session['cart'] = cart

    if added_items > 0:
        return jsonify({
            'success': True, 
            'message': f'เพิ่ม {added_items} รายการลงตะกร้าแล้ว'
        })
    else:
        return jsonify({
            'success': False, 
            'message': 'ไม่มีสินคาที่สามารถเพิ่มได้ (สินค้าอาจหมดหรือไม่พร้อมจำหน่าย)'
        })

# ========================
# Admin Routes
# ========================

@app.route('/admin')
def admin():
    """หน้าแอดมิน"""
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect(url_for('index'))

    conn = get_db_connection()
    products = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        ORDER BY p.created_at DESC
    """).fetchall()

    categories = get_categories()

    # Statistics
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM products) as total_products,
            (SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now')) as today_orders,
            (SELECT COUNT(*) FROM users WHERE role = 'customer') as total_users,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE date(created_at) = date('now')) as today_revenue
    """).fetchone()

    conn.close()

    return render_template('admin.html', 
                         products=products, 
                         categories=categories,
                         stats=stats)

@app.route('/admin/orders')
def admin_orders():
    """หน้าจัดการคำสั่งซื้อ"""
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect(url_for('index'))

    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.*, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()

    return render_template('admin_orders.html', orders=orders)

# ========================
# Admin API Routes (Complete)
# ========================

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    """เพิ่มสินค้าใหม่ (รับ JSON)"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json() or {}
    try:
        name = data['name']
        price = float(data['price'])
        category_id = int(data['category_id'])
    except Exception:
        return jsonify({'success': False, 'message': 'ข้อมูลไม่ครบหรือรูปแบบไม่ถูกต้อง'})

    name_en = data.get('name_en', '')
    description = data.get('description', '')
    image = data.get('image', '')
    is_available = 1 if data.get('is_available', True) else 0
    is_featured = 1 if data.get('is_featured', False) else 0
    stock_quantity = int(data.get('stock_quantity', 0))

    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO products 
            (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity))
        conn.commit()
        product_id = cursor.lastrowid
        return jsonify({'success': True, 'message': 'เพิ่มสินค้าเรียบร้อยแล้ว', 'product_id': product_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    """อัปเดตสินค้า (รับ JSON)"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json() or {}

    # Build updated values (validate minimal required)
    try:
        name = data['name']
        price = float(data['price'])
        category_id = int(data['category_id'])
    except Exception:
        return jsonify({'success': False, 'message': 'ข้อมูลไม่ครบหรือรูปแบบไม่ถูกต้อง'})

    name_en = data.get('name_en', '')
    description = data.get('description', '')
    image = data.get('image', '')
    is_available = 1 if data.get('is_available', True) else 0
    is_featured = 1 if data.get('is_featured', False) else 0
    stock_quantity = int(data.get('stock_quantity', 0))

    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE products SET
            name = ?, name_en = ?, description = ?, price = ?,
            image = ?, category_id = ?, is_available = ?, is_featured = ?, stock_quantity = ?
            WHERE id = ?
        """, (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity, product_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'อัปเดตสินค้าเรียบร้อยแล้ว'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """ลบสินค้า"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'ลบสินค้าเรียบร้อยแล้ว'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/toggle_product_status/<int:product_id>', methods=['POST'])
def toggle_product_status(product_id):
    """เปิด/ปิดสถานะสินค้า"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json() or {}
    new_status = 1 if data.get('status', True) else 0

    conn = get_db_connection()
    try:
        conn.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_status, product_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'อัปเดตสถานะเรียบร้อยแล้ว'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/toggle_product_featured/<int:product_id>', methods=['POST'])
def toggle_product_featured(product_id):
    """เปิด/ปิดสถานะแนะนำ"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json() or {}
    new_featured = 1 if data.get('featured', False) else 0

    conn = get_db_connection()
    try:
        conn.execute("UPDATE products SET is_featured = ? WHERE id = ?", (new_featured, product_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'อัปเดตสถานะแนะนำเรียบร้อยแล้ว'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    """อัปเดตสถานะคำสั่งซื้อ"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json() or {}
    new_status = data.get('status')

    valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'สถานะไม่ถูกต้อง'})

    conn = get_db_connection()
    try:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'อัปเดตสถานะเรียบร้อยแล้ว'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/print_order/<int:order_id>')
def print_order(order_id):
    """พิมพ์คำสั่งซื้อ"""
    if session.get('role') != 'admin':
        flash('ไม่มีสิทธิ์เข้าถึง')
        return redirect(url_for('index'))

    conn = get_db_connection()

    # Get order details
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not order:
        flash('ไม่พบคำสั่งซื้อ')
        conn.close()
        return redirect(url_for('admin_orders'))

    # Get order items
    order_items = conn.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()

    conn.close()

    # Return a simple HTML page for printing
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>คำสั่งซื้อ #{order['id']}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .order-info {{ margin: 20px 0; }}
            .order-info div {{ margin: 5px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .total {{ font-weight: bold; background-color: #f9f9f9; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body onload="window.print(); window.close();">
        <div class="header">
            <h2>🍰 Sweet Dreams Bakery</h2>
            <p>เบเกอรี่พรีเมียมคุณภาพสูง</p>
            <h3>ใบสั่งซื้อ #{order['id']}</h3>
        </div>

        <div class="order-info">
            <div><strong>วันที่สั่ง:</strong> {order['created_at']}</div>
            <div><strong>ลูกค้า:</strong> {order['customer_name']}</div>
            <div><strong>เบอร์โทร:</strong> {order['customer_phone']}</div>
            {'<div><strong>ที่อยู่:</strong> ' + order['customer_address'] + '</div>' if order['customer_address'] else ''}
            <div><strong>สถานะ:</strong> {order['status']}</div>
            {'<div><strong>หมายเหตุ:</strong> ' + order['notes'] + '</div>' if order['notes'] else ''}
        </div>

        <table>
            <thead>
                <tr>
                    <th>รายการสินค้า</th>
                    <th style="text-align: center;">จำนวน</th>
                    <th style="text-align: right;">ราคาต่อหน่วย</th>
                    <th style="text-align: right;">รวม</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''<tr>
                    <td>{item["product_name"]}{(" (" + item["options"] + ")") if item["options"] else ""}</td>
                    <td style="text-align: center;">{item["quantity"]}</td>
                    <td style="text-align: right;">{item["unit_price"]:.0f} บาท</td>
                    <td style="text-align: right;">{item["total_price"]:.0f} บาท</td>
                </tr>''' for item in order_items])}
                <tr class="total">
                    <td colspan="3" style="text-align: right;"><strong>รวมทั้งสิ้น</strong></td>
                    <td style="text-align: right;"><strong>{order['total_amount']:.0f} บาท</strong></td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <p>ขอบคุณที่ใช้บริการ Sweet Dreams Bakery</p>
            <p>📍 123 ถนนพหลโยธิน เชียงราย 57000 | ☎️ 089-123-4567</p>
            <p>🕒 เปิดทุกวัน 07:00 - 20:00</p>
        </div>
    </body>
    </html>
    """

# ========================
# Error Handlers
# ========================

# ========================
# Initialize Application
# ========================

def create_default_images_folder():
    """สร้างโฟลเดอร์รูปภาพเริ่มต้น"""
    images_path = os.path.join('static', 'images', 'products')
    if not os.path.exists(images_path):
        os.makedirs(images_path, exist_ok=True)
        print(f"📁 Created images folder: {images_path}")


if __name__ == "__main__":
    # สร้างฐานข้อมูลและข้อมูลเริ่มต้น
    print("🔧 Initializing Sweet Dreams Bakery...")

    init_db()
    print("✅ Database initialized")

    seed_categories()
    print("✅ Categories seeded")

    seed_products()
    print("✅ Products seeded")

    create_admin_user()
    print("✅ Admin user created")

    create_default_images_folder()
    print("✅ Images folder created")

    print("\n" + "="*50)
    print("🍰 Sweet Dreams Bakery Server Starting...")
    print("="*50)
    print("🌐 Main Website: http://localhost:5000")
    print("🔐 Admin Panel: http://localhost:5000/admin")
    print("📦 Manage Orders: http://localhost:5000/admin/orders")
    print("👤 Admin Login: username=admin, password=admin123")
    print("="*50)
    print("📝 Features Available:")
    print("   ✅ Product Management (Add/Edit/Delete)")
    print("   ✅ Order Management")
    print("   ✅ User Authentication")
    print("   ✅ Shopping Cart")
    print("   ✅ User Profiles")
    print("   ✅ Order History")
    print("   ✅ Responsive Design")
    print("="*50)

    app.run(debug=True, host='0.0.0.0', port=5000)
