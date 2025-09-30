
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps
import base64
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = "sweetdreams_bakery_secret_2024"
app.permanent_session_lifetime = timedelta(days=7)
DB_NAME = "bakery.db"

@app.template_filter('to_bangkok')
def to_bangkok_filter(value, fmt='%d/%m/%Y %H:%M'):
    if not value:
        return "N/A"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    dt = value.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Bangkok"))
    return dt.strftime(fmt)

# ========================
# Database Functions
# ========================

def init_db():
    """สร้างตารางฐานข้อมูล"""
    conn = sqlite3.connect(DB_NAME)
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
        is_available BOOLEAN DEFAULT 1,
        is_featured BOOLEAN DEFAULT 0,
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status TEXT DEFAULT 'unpaid',
    paid_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_status_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipient_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT,
        province TEXT,
        postal_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('กรุณาเข้าสู่ระบบก่อนสั่งซื้อ')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def seed_categories():
    """เพิ่มหมวดหมู่เริ่มต้น"""
    conn = sqlite3.connect(DB_NAME)
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

# def seed_products():
#     """เพิ่มหมวดหมู่ตัวอย่าง (ไม่เพิ่มซ้ำ)"""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     categories = [
#         ("เค้ก", "Cake", "fas fa-birthday-cake", "เค้กหลากหลายรสชาติ", 1),
#         ("ขนมปัง", "Bread", "fas fa-bread-slice", "ขนมปังอบสดใหม่", 2),
#         ("เครื่องดื่ม", "Beverage", "fas fa-coffee", "กาแฟและเครื่องดื่ม", 3),
#         ("ขนมหวาน", "Dessert", "fas fa-ice-cream", "ขนมหวานและของว่าง", 4),
#     ]
#     for cat in categories:
#         cursor.execute("SELECT id FROM categories WHERE name = ?", (cat[0],))
#         if cursor.fetchone():
#             continue
#         cursor.execute("""
#             INSERT INTO categories (name, name_en, icon, description, display_order)
#             VALUES (?, ?, ?, ?, ?)
#         """, cat)
#     conn.commit()
#     conn.close()

def seed_products():
    """เพิ่มสินค้าตัวอย่าง (ไม่เพิ่มซ้ำ)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # ดึง id ของแต่ละหมวดหมู่
    cursor.execute("SELECT id, name FROM categories")
    categories = {name: id for id, name in cursor.fetchall()}
    products = [
        # name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity
        ("เค้กช็อกโกแลต", "Chocolate Cake", "เค้กช็อกโกแลตเข้มข้น", 120, "chocolate_cake.jpg", categories.get("เค้ก"), 1, 1, 10),
        ("ขนมปังฝรั่งเศส", "Baguette", "ขนมปังฝรั่งเศสอบสด", 60, "baguette.jpg", categories.get("ขนมปัง"), 1, 0, 15),
        ("ลาเต้เย็น", "Iced Latte", "กาแฟลาเต้เย็นหอมกรุ่น", 65, "iced_latte.jpg", categories.get("เครื่องดื่ม"), 1, 1, 20),
        ("บราวนี่", "Brownie", "บราวนี่ช็อกโกแลตเข้มข้น", 55, "brownie.jpg", categories.get("ขนมหวาน"), 1, 0, 12),
        ("เค้กส้ม", "Orange Cake", "เค้กส้มสดใหม่", 110, "orange_cake.jpg", categories.get("เค้ก"), 1, 1, 8),
        ("ครัวซองต์", "Croissant", "ครัวซองต์เนยสด", 45, "croissant.jpg", categories.get("ขนมปัง"), 1, 0, 18),
        ("ชาเขียวเย็น", "Iced Green Tea", "ชาเขียวเย็นสูตรพิเศษ", 55, "iced_greentea.jpg", categories.get("เครื่องดื่ม"), 1, 0, 25),
        ("มาการอง", "Macaron", "มาการองหลากรส", 35, "macaron.jpg", categories.get("ขนมหวาน"), 1, 0, 30),
        ("เค้กเรดเวลเวท", "Red Velvet Cake", "เค้กเรดเวลเวทเนื้อนุ่ม", 130, "red_velvet.jpg", categories.get("เค้ก"), 1, 1, 7),
    ]
    for product in products:
        # ตรวจสอบก่อน insert ว่ามีชื่อซ้ำหรือยัง
        cursor.execute("SELECT id FROM products WHERE name = ?", (product[0],))
        if cursor.fetchone():
            continue
        cursor.execute("""
            INSERT INTO products 
            (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, product)
    conn.commit()
    conn.close()

def create_admin_user():
    """สร้างผู้ใช้แอดมินเริ่มต้น"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    admin_password = generate_password_hash("admin123")
    cursor.execute("""
        INSERT OR IGNORE INTO users 
        (username, email, password, full_name, role) 
        VALUES (?, ?, ?, ?, ?)
    """, ("admin", "admin@sweetdreams.com", admin_password, "ผู้ดูแลระบบ", "admin"))
    conn.commit()
    conn.close()

def create_default_images_folder():
    """สร้างโฟลเดอร์รูปภาพเริ่มต้น"""
    images_path = os.path.join('static', 'images', 'products')
    if not os.path.exists(images_path):
        os.makedirs(images_path, exist_ok=True)
        print(f"Created images folder: {images_path}")

# ========================
# Helper Functions
# ========================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return user

def get_categories():
    conn = get_db_connection()
    categories = conn.execute(
        "SELECT * FROM categories ORDER BY display_order"
    ).fetchall()
    conn.close()
    return categories

def get_products_by_category(category_id=None, featured_only=False):
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
    cart = session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values())
    total_price = sum(item['quantity'] * item['price'] for item in cart.values())
    return total_items, total_price

# ========================
# Context Processor
# ========================

@app.context_processor
def inject_global_data():
    categories = get_categories()
    cart_total_items, _ = get_cart_total()
    return dict(
        categories=categories,
        cart_total_items=cart_total_items
    )

# ========================
# Routes - Main Pages
# ========================

@app.route('/')
def index():
    categories = get_categories()
    featured_products = get_products_by_category(featured_only=True)
    all_products = get_products_by_category()
    # กรองสินค้าไม่ให้ซ้ำ (โดย id)
    unique_products = []
    seen_ids = set()
    for product in all_products:
        if product['id'] not in seen_ids:
            unique_products.append(product)
            seen_ids.add(product['id'])
    products_by_category = {}
    for product in unique_products:
        category_name = product['category_name']
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)
    return render_template('index.html',
                         featured_products=featured_products,
                         products_by_category=products_by_category)

@app.route('/category/<int:category_id>')
def category_by_id(category_id):
    categories = get_categories()
    products = get_products_by_category(category_id)
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

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash('ไม่พบสินค้าที่ต้องการ')
        return redirect(url_for('index'))
    return render_template('product_detail.html', product=product)

# ========================
# Authentication Routes
# ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get("remember-me")

        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session.permanent = True if remember else False

            resp = make_response(redirect(url_for('admin') if user['role'] == 'admin' else url_for('index')))

            if remember:
                # เก็บ username + password ใน cookie
                resp.set_cookie('remembered_username', username, max_age=30*24*60*60)
                encoded_password = base64.b64encode(password.encode()).decode()
                resp.set_cookie('remembered_password', encoded_password, max_age=30*24*60*60)
            else:
                resp.set_cookie('remembered_username', '', expires=0)
                resp.set_cookie('remembered_password', '', expires=0)

            return resp
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    # GET request → อ่าน cookie
    remembered_username = request.cookies.get('remembered_username', '')
    remembered_password = request.cookies.get('remembered_password', '')
    if remembered_password:
        remembered_password = base64.b64decode(remembered_password).decode()
    return render_template('login.html', remembered_username=remembered_username, remembered_password=remembered_password)



@app.route('/register', methods=['GET', 'POST'])
def register():
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
            return render_template('register.html')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            # TODO: ส่งอีเมล reset password (SMTP)
            flash("เราได้ส่งลิงก์รีเซ็ตรหัสผ่านไปที่อีเมลของคุณแล้ว", "info")
        else:
            flash("ไม่พบอีเมลนี้ในระบบ", "danger")

    return render_template('forgot_password.html')


@app.route('/logout')
def logout():
    remember_username = request.cookies.get('remembered_username', '')
    remember_password = request.cookies.get('remembered_password', '')
    session.clear()
    resp = make_response(redirect(url_for('login')))
    # ถ้ามี cookie เก็บ username+password อยู่แล้วก็ให้มันเด้งต่อ
    if remember_username and remember_password:
        resp.set_cookie('remembered_username', remember_username, max_age=30*24*60*60)
        resp.set_cookie('remembered_password', remember_password, max_age=30*24*60*60)
    return resp

# ========================
# Cart Management Routes
# ========================

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    total_items, total_price = get_cart_total()
    return render_template('cart.html',
                         cart_items=cart_items,
                         total_items=total_items,
                         total_price=total_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = max(1, int(data.get('quantity', 1)))  # กันค่าติดลบ/ศูนย์
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
    session.modified = True

    total_items, total_price = get_cart_total()
    return jsonify({
        'success': True,
        'message': f'เพิ่ม {product["name"]} ลงในตะกร้าแล้ว',
        'total_items': total_items,
        'total_price': total_price
    })

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    cart_key = str(data.get('cart_key'))  # 👉 ใช้ชื่อให้ตรงกับ key
    quantity = int(data.get('quantity', 1))

    cart = session.get('cart', {})

    if cart_key in cart:
        if quantity > 0:
            cart[cart_key]['quantity'] = quantity
        else:
            # ถ้าใส่ 0 หรือติดลบ → ลบออก
            cart.pop(cart_key)

        session['cart'] = cart
        session.modified = True

        total_items, total_price = get_cart_total()
        return jsonify({
            'success': True,
            'total_items': total_items,
            'total_price': total_price
        })

    return jsonify({'success': False, 'message': 'ไม่พบสินค้า'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = str(data.get('cart_key'))

    cart = session.get('cart', {})

    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart

        total_items = sum(item['quantity'] for item in cart.values())
        total_price = sum(item['price'] * item['quantity'] for item in cart.values())

        return jsonify({
            'success': True,
            'total_items': total_items,
            'total_price': total_price
        })

    return jsonify({'success': False, 'message': 'ไม่พบสินค้า'})


@app.route('/clear_cart', methods=['POST'])
def clear_cart():
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
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('ตะกร้าสินค้าว่าง')
        return redirect(url_for('index'))

    conn = get_db_connection()
    addresses = conn.execute("""
        SELECT id,
               address || 
               CASE WHEN city IS NOT NULL THEN ', ' || city ELSE '' END ||
               CASE WHEN postal_code IS NOT NULL THEN ', ' || postal_code ELSE '' END ||
               CASE WHEN province IS NOT NULL THEN ', ' || province ELSE '' END
               AS full_address
        FROM addresses
        WHERE user_id = ?
    """, (session['user_id'],)).fetchall()
    conn.close()

    total_items, total_price = get_cart_total()

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        customer_address_id = request.form.get('customer_address')
        notes = request.form.get('notes', '')

        # ดึงที่อยู่จริงจาก id
        conn = get_db_connection()
        address_row = conn.execute("SELECT * FROM addresses WHERE id = ?", (customer_address_id,)).fetchone()
        customer_address = f"{address_row['recipient_name']}, {address_row['address']}, {address_row['city'] or ''}, {address_row['postal_code'] or ''}, {address_row['province'] or ''}"

        try:
            cursor = conn.execute("""
                INSERT INTO orders 
                (user_id, total_amount, customer_name, customer_phone, customer_address, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (session['user_id'], total_price, customer_name, customer_phone, customer_address, notes))
            order_id = cursor.lastrowid

            # เพิ่ม order_items และลด stock
            for item in cart.values():
                # เพิ่ม order_items
                conn.execute("""
                    INSERT INTO order_items 
                    (order_id, product_id, quantity, unit_price, total_price, options)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item['id'], item['quantity'], item['price'], item['price'] * item['quantity'], item.get('options', '')))

                # ลด stock ของสินค้า
                conn.execute("""
                    UPDATE products
                    SET stock_quantity = stock_quantity - ?
                    WHERE id = ? AND stock_quantity >= ?
                """, (item['quantity'], item['id'], item['quantity']))

                # ตรวจสอบ stock เพียงพอ
                if conn.total_changes == 0:
                    raise Exception(f"สินค้ารหัส {item['id']} มีไม่เพียงพอ")

            conn.commit()
            session['cart'] = {}
            flash(f'ขอบคุณสำหรับคำสั่งซื้อ! หมายเลขคำสั่งซื้อ: #{order_id}')
            return redirect(url_for('order_detail', order_id=order_id))
        except Exception as e:
            conn.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}')
        finally:
            conn.close()

    return render_template('checkout.html',
                           cart_items=cart,
                           total_items=total_items,
                           total_price=total_price,
                           addresses=addresses)


# ========================
# User Profile Routes
# ========================

@app.route('/profile')
def profile():
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

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อน")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    full_name = request.form.get("full_name", "")
    phone = request.form.get("phone", "")
    address = request.form.get("address", "")
    birthday = request.form.get("birthday", "")

    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE users
            SET full_name = ?, phone = ?, address = ?, birthday = ?
            WHERE id = ?
        """, (full_name, phone, address, birthday, user_id))
        conn.commit()
        flash("อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว")
    except Exception as e:
        conn.rollback()
        flash(f"เกิดข้อผิดพลาด: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for("profile"))

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    # ตรวจสอบล็อกอิน
    user_id = session.get("user_id")
    if not user_id:
        flash("กรุณาเข้าสู่ระบบก่อน")
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        flash("ไม่พบผู้ใช้นี้")
        conn.close()
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # ตรวจสอบรหัสผ่านเก่า
        if not check_password_hash(user["password"], current_password):
            flash("รหัสผ่านเก่าไม่ถูกต้อง")
            return redirect(url_for("change_password"))

        # ตรวจสอบรหัสผ่านใหม่ตรงกัน
        if new_password != confirm_password:
            flash("รหัสผ่านใหม่ไม่ตรงกัน")
            return redirect(url_for("change_password"))

        # อัปเดตรหัสผ่านใหม่ใน DB
        hashed_password = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        conn.close()

        flash("เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")
        return redirect(url_for("profile"))

    conn.close()
    return render_template("change_password.html")


# ========================
# Order Routes
# ========================

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    
    if not order:
        conn.close()
        return "ไม่พบคำสั่งซื้อ", 404

    # แปลง Row เป็น dict
    order = dict(order)

    # แปลง created_at เป็น datetime
    if order.get("created_at"):
        try:
            order["created_at"] = datetime.fromisoformat(order["created_at"])
        except ValueError:
            order["created_at"] = None

    # ดึงที่อยู่ล่าสุดของผู้ใช้
    addr = None
    if order.get('user_id'):
        addr_row = conn.execute("""
            SELECT *,
                   address || 
                   CASE WHEN city IS NOT NULL THEN ', ' || city ELSE '' END ||
                   CASE WHEN postal_code IS NOT NULL THEN ', ' || postal_code ELSE '' END ||
                   CASE WHEN province IS NOT NULL THEN ', ' || province ELSE '' END
                   AS full_address
            FROM addresses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (order['user_id'],)).fetchone()
        if addr_row:
            addr = dict(addr_row)

    # ตรวจสอบสิทธิ์: ผู้ใช้ปกติดูได้เฉพาะของตัวเอง
    if session.get("role") != "admin":
        if session.get("user_id") != order.get("user_id"):
            conn.close()
            flash("คุณไม่มีสิทธิ์เข้าดูคำสั่งซื้อนี้")
            return redirect(url_for("order_history"))

    # ดึงสินค้า
    items = conn.execute("""
        SELECT oi.*, p.name AS product_name, p.price AS product_price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()

    # แปลง Row เป็น dict
    items = [dict(i) for i in items]

    conn.close()
    return render_template("order_detail.html", order=order, addr=addr, items=items)


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    conn = get_db_connection()
    
    # ตรวจสอบสิทธิ์: admin หรือเจ้าของคำสั่งซื้อ
    if session.get('role') == 'admin':
        order = conn.execute("""
            SELECT * FROM orders 
            WHERE id = ? AND status = 'pending'
        """, (order_id,)).fetchone()
    else:
        order = conn.execute("""
            SELECT * FROM orders 
            WHERE id = ? AND user_id = ? AND status = 'pending'
        """, (order_id, session.get('user_id'))).fetchone()

    if not order:
        conn.close()
        return jsonify({'success': False, 'message': 'ไม่พบคำสั่งซื้อหรือไม่สามารถยกเลิกได้'})

    try:
        items = conn.execute("""
            SELECT product_id, quantity FROM order_items WHERE order_id = ?
        """, (order_id,)).fetchall()

        for item in items:
            conn.execute("""
                UPDATE products
                SET stock_quantity = stock_quantity + ?
                WHERE id = ?
            """, (item['quantity'], item['product_id']))

        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'ยกเลิกคำสั่งซื้อเรียบร้อยแล้ว และคืนจำนวนสินค้าแล้ว'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})


@app.route('/reorder/<int:order_id>', methods=['POST'])
def reorder(order_id):
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'กรุณาเข้าสู่ระบบ'})
    conn = get_db_connection()
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
            'message': 'ไม่มีสินค้าที่สามารถเพิ่มได้ (สินค้าอาจหมดหรือไม่พร้อมจำหน่าย)'
        })

# ========================
# Admin Routes
# ========================

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect(url_for('index'))
    conn = get_db_connection()
    products = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        ORDER BY p.created_at DESC
    """).fetchall()
    categories = get_categories()    # --- เพิ่มสถิติรายวัน ---
    # นับเฉพาะ order ที่ไม่ถูกยกเลิก
    orders_today = conn.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now') AND status != 'cancelled'").fetchone()[0]
    new_users_today = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer' AND date(created_at) = date('now')").fetchone()[0]
    # ยอดขายวันนี้นับเฉพาะ order ที่เสร็จสิ้น
    revenue_today = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE date(created_at) = date('now') AND status = 'completed'").fetchone()[0]
    conn.close()
    return render_template('admin.html', 
                         products=products, 
                         categories=categories,
                         orders_today=orders_today,
                         new_users_today=new_users_today,
                         revenue_today=revenue_today)

@app.route('/admin/orders')
def admin_orders():
    # ตรวจสอบสิทธิ์แอดมิน
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect(url_for('index'))

    conn = get_db_connection()
    
    # ดึงคำสั่งซื้อทั้งหมด
    orders_raw = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    orders = []

    for order_row in orders_raw:
        order = dict(order_row)  # แปลง Row เป็น dict

        # แปลง created_at เป็น datetime
        if order.get('created_at'):
            try:
                order['created_at'] = datetime.strptime(order['created_at'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                order['created_at'] = None

        # ดึงที่อยู่ผู้รับ
        if order.get('address_id'):
            addr = conn.execute(
                "SELECT * FROM addresses WHERE id=?",
                (order['address_id'],)
            ).fetchone()
            if addr:
                order['address'] = f"{addr['address']}, {addr.get('city','')}, {addr.get('province','')}, {addr.get('postal_code','')}"
            else:
                order['address'] = '-'
        else:
            order['address'] = '-'

        # ดึงรายการสินค้า
        items_raw = conn.execute(
            """
            SELECT oi.*, p.name AS product_name, p.price AS unit_price
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id=?
            """,
            (order['id'],)
        ).fetchall()

        items = []
        for item in items_raw:
            items.append({
                'product_name': item['product_name'] or '-',
                'quantity': item['quantity'],
                'price': float(item['unit_price'] or 0),
                'total': float(item['quantity'] * (item['unit_price'] or 0))
            })

        order['items'] = items
        order['item_count'] = len(items)
        # คำนวณยอดรวมทั้งหมด
        order['total_amount'] = sum(i['total'] for i in items)

        orders.append(order)

    conn.close()
    return render_template('admin_orders.html', orders=orders)


@app.route("/admin/print_order/<int:order_id>")
def admin_print_order(order_id):
    if session.get('role') != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect(url_for('index'))

    conn = get_db_connection()
    
    try:
        # ดึงข้อมูลคำสั่งซื้อ พร้อมข้อมูลลูกค้า
        order_row = conn.execute("""
            SELECT o.*, u.email as customer_email, u.username
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (order_id,)).fetchone()
        
        if not order_row:
            flash('ไม่พบคำสั่งซื้อ')
            return redirect(url_for('admin_orders'))

        # แปลง Row เป็น dict
        order = dict(order_row)

        # แปลง created_at เป็น datetime object
        if order.get("created_at"):
            try:
                if isinstance(order["created_at"], str):
                    # ลองหลายรูปแบบ datetime
                    formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f"
                    ]
                    
                    parsed_date = None
                    for fmt in formats:
                        try:
                            parsed_date = datetime.strptime(order["created_at"], fmt)
                            break
                        except ValueError:
                            continue
                    
                    order["created_at"] = parsed_date or datetime.now()
            except (ValueError, TypeError):
                order["created_at"] = datetime.now()

        # ดึงรายการสินค้า พร้อมชื่อสินค้า
        items_rows = conn.execute("""
            SELECT oi.*, p.name as product_name, p.image as product_image
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            ORDER BY oi.id
        """, (order_id,)).fetchall()
        
        # แปลง items เป็น list of dict
        items = [dict(item) for item in items_rows]

        # คำนวณข้อมูลเพิ่มเติม
        order['item_count'] = len(items)
        
        # คำนวณยอดรวมใหม่ถ้าไม่มี (เผื่อข้อมูลเสีย)
        if not order.get('total_amount') or order['total_amount'] == 0:
            order['total_amount'] = sum(
                item.get('total_price', 0) or 
                (item.get('quantity', 0) * item.get('unit_price', 0))
                for item in items
            )

        # ดึงที่อยู่ลูกค้า (แก้ไขให้ใช้ user_id จาก order แทน session)
        addr = None
        if order.get('user_id'):
            addr_rows = conn.execute("""
                SELECT *,
                       address || 
                       CASE WHEN city IS NOT NULL THEN ', ' || city ELSE '' END ||
                       CASE WHEN postal_code IS NOT NULL THEN ', ' || postal_code ELSE '' END ||
                       CASE WHEN province IS NOT NULL THEN ', ' || province ELSE '' END
                       AS full_address
                FROM addresses
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
            """, (order['user_id'],)).fetchone()
            
            if addr_rows:
                addr = dict(addr_rows)

        return render_template(
            "print_order.html",
            order=order,
            items=items,
            addr=addr,
            now=datetime.now(),
            show_qr=True  # เปิดใช้ QR code
        )
        
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect(url_for('admin_orders'))
    finally:
        conn.close()


# เพิ่ม route สำหรับส่งอีเมลใบเสร็จ
@app.route('/send_receipt_email', methods=['POST'])
def send_receipt_email():
    """ส่งใบเสร็จทางอีเมล"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})
    
    data = request.get_json()
    order_id = data.get('id')
    customer_email = data.get('customer_email')
    customer_name = data.get('customer_name', 'ลูกค้า')
    
    if not order_id or not customer_email:
        return jsonify({'success': False, 'message': 'ข้อมูลไม่ครบถ้วน'})
    
    try:
        # TODO: ติดตั้งและตั้งค่า SMTP สำหรับส่งอีเมล
        # ตัวอย่าง:
        # from flask_mail import Mail, Message
        # 
        # msg = Message(
        #     subject=f'ใบเสร็จ Sweet Dreams Bakery #{order_id}',
        #     recipients=[customer_email],
        #     html=render_template('email_receipt.html', order_id=order_id)
        # )
        # mail.send(msg)
        
        # สำหรับตอนนี้แค่ log
        print(f"Would send receipt #{order_id} to {customer_email}")
        
        return jsonify({
            'success': True,
            'message': f'ส่งใบเสร็จไปที่ {customer_email} เรียบร้อยแล้ว'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })


# เพิ่ม route สำหรับ thermal printer API
@app.route('/api/thermal-print', methods=['POST'])
def thermal_print():
    """พิมพ์ผ่านเครื่องพิมพ์ thermal"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})
    
    data = request.get_json()
    content = data.get('content', '')
    
    if not content:
        return jsonify({'success': False, 'message': 'ไม่มีข้อมูลสำหรับพิมพ์'})
    
    try:
        # TODO: เชื่อมต่อกับ thermal printer
        # ตัวอย่าง:
        # import win32print
        # import win32api
        # 
        # printer_name = win32print.GetDefaultPrinter()
        # hPrinter = win32print.OpenPrinter(printer_name)
        # 
        # try:
        #     hJob = win32print.StartDocPrinter(hPrinter, 1, ("Receipt", None, "RAW"))
        #     win32print.StartPagePrinter(hPrinter)
        #     win32print.WritePrinter(hPrinter, content.encode('utf-8'))
        #     win32print.EndPagePrinter(hPrinter)
        #     win32print.EndDocPrinter(hPrinter)
        # finally:
        #     win32print.ClosePrinter(hPrinter)
        
        # สำหรับตอนนี้แค่ log
        print(f"Would print thermal receipt:\n{content}")
        
        return jsonify({
            'success': True,
            'message': 'พิมพ์ใบเสร็จสำเร็จ'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })


# เพิ่มฟังก์ชันช่วยสำหรับจัดการ datetime
def safe_datetime_parse(date_string, default=None):
    """แปลง string เป็น datetime อย่างปลอดภัย"""
    if not date_string:
        return default or datetime.now()
    
    if isinstance(date_string, datetime):
        return date_string
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return default or datetime.now()


# ปรับปรุง template filter
@app.template_filter('safe_datetime')
def safe_datetime_filter(value, format='%d/%m/%Y %H:%M'):
    """Template filter สำหรับแสดง datetime อย่างปลอดภัย"""
    try:
        if isinstance(value, str):
            value = safe_datetime_parse(value)
        elif not isinstance(value, datetime):
            return 'ไม่ระบุ'
        
        return value.strftime(format)
    except (ValueError, AttributeError):
        return 'ไม่ระบุ'


@app.template_filter('format_currency')
def format_currency(value):
    """Format ตัวเลขเป็นสกุลเงิน"""
    try:
        return "{:,.0f}".format(float(value or 0))
    except (ValueError, TypeError):
        return "0"


# ปรับปรุงการจัดการ order status
def get_status_text(status):
    """แปลง status เป็นข้อความไทย"""
    status_map = {
        'pending': 'รอดำเนินการ',
        'processing': 'กำลังจัดเตรียม',
        'completed': 'เสร็จสิ้น',
        'cancelled': 'ยกเลิกแล้ว'
    }
    return status_map.get(status, status)


@app.template_filter('status_text')
def status_text_filter(status):
    """Template filter สำหรับแสดงสถานะ"""
    return get_status_text(status)
@app.route("/admin/order_history")
def admin_order_history():
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.*, u.username, u.email
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()

    return render_template("admin_order_history.html", orders=orders)

# ========================
# Admin API Routes
# ========================

@app.route('/admin/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'ไม่พบสินค้า'}), 404


@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO products (name, name_en, description, price, image, category_id, is_available, is_featured, stock_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], data.get('name_en'), data.get('description'), data['price'],
        data.get('image'), data['category_id'], data.get('is_available', 0),
        data.get('is_featured', 0), data.get('stock_quantity', 0)
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('''
        UPDATE products SET 
            name=?, name_en=?, description=?, price=?, image=?, 
            category_id=?, is_available=?, is_featured=?, stock_quantity=?
        WHERE id=?
    ''', (
        data['name'], data.get('name_en'), data.get('description'), data['price'],
        data.get('image'), data['category_id'], data.get('is_available', 0),
        data.get('is_featured', 0), data.get('stock_quantity', 0), product_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/admin/toggle_product_status/<int:product_id>', methods=['POST'])
def toggle_product_status(product_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    product = conn.execute('SELECT is_available FROM products WHERE id=?', (product_id,)).fetchone()
    if product:
        new_status = 0 if product['is_available'] else 1
        conn.execute('UPDATE products SET is_available=? WHERE id=?', (new_status, product_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_status': new_status})
    conn.close()
    return jsonify({'success': False, 'message': 'ไม่พบสินค้า'}), 404


@app.route('/admin/toggle_product_featured/<int:product_id>', methods=['POST'])
def toggle_product_featured(product_id):
    if session.get('role') != 'admin':
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    product = conn.execute('SELECT is_featured FROM products WHERE id=?', (product_id,)).fetchone()
    if product:
        new_featured = 0 if product['is_featured'] else 1
        conn.execute('UPDATE products SET is_featured=? WHERE id=?', (new_featured, product_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_featured': new_featured})
    conn.close()
    return jsonify({'success': False, 'message': 'ไม่พบสินค้า'}), 404

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'})

    data = request.get_json()
    new_status = data.get('status')

    valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'สถานะไม่ถูกต้อง'})

    conn = get_db_connection()
    try:
        order = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'ไม่พบคำสั่งซื้อ'})

        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'อัปเดตสถานะคำสั่งซื้อ #{order_id} เป็น {new_status} แล้ว'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})
    finally:
        conn.close()

@app.route('/admin/print_order/<int:order_id>')
def print_order(order_id):
    if session.get('role') != 'admin':
        flash('ไม่มีสิทธิ์เข้าถึง')
        return redirect(url_for('index'))
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        flash('ไม่พบคำสั่งซื้อ')
        conn.close()
        return redirect(url_for('admin_orders'))
    order_items = conn.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()
    conn.close()
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
            <h2>Sweet Dreams Bakery</h2>
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
            <p>123 ถนนพหลโยธิน เชียงราย 57000 | 089-123-4567</p>
            <p>เปิดทุกวัน 07:00 - 20:00</p>
        </div>
    </body>
    </html>
    """

# ========================
# Error Handlers
# ========================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route("/order_history")
def order_history():
    user_id = session.get("user_id")
    is_admin = session.get("is_admin", False)  # สมมติคุณเก็บสิทธิ์แอดมินใน session

    if not user_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    
    if is_admin:
        # แอดมินเห็นคำสั่งซื้อทั้งหมด พร้อม username ของผู้สั่ง
        orders = conn.execute("""
            SELECT o.*, u.username
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """).fetchall()
    else:
        # ผู้ใช้ทั่วไปเห็นแค่คำสั่งซื้อของตัวเอง
        orders = conn.execute("""
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
    
    conn.close()

    return render_template("order_history.html", orders=orders, is_admin=is_admin)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y'):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format)
    except:
        return value

@app.route("/address_book")
def address_book():
    user_id = session.get("user_id")
    if not user_id:
        flash("กรุณาเข้าสู่ระบบก่อนใช้งาน")
        return redirect(url_for("login"))

    conn = get_db_connection()
    addresses = conn.execute(
        "SELECT * FROM addresses WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return render_template("address_book.html", addresses=addresses)


@app.route("/address_book/add", methods=["GET", "POST"])
def add_address():
    user_id = session.get("user_id")
    if not user_id:
        flash("กรุณาเข้าสู่ระบบก่อนใช้งาน")
        return redirect(url_for("login"))

    if request.method == "POST":
        recipient_name = request.form["recipient_name"]
        phone = request.form["phone"]
        address = request.form["address"]
        city = request.form.get("city", "")
        postal_code = request.form.get("postal_code", "")
        province = request.form.get("province", "")

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO addresses (user_id, recipient_name, phone, address, city, postal_code, province)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, recipient_name, phone, address, city, postal_code, province))
                    
        conn.commit()
        conn.close()

        flash("เพิ่มที่อยู่เรียบร้อยแล้ว")
        return redirect(url_for("address_book"))

    return render_template("address_form.html", action="เพิ่มที่อยู่ใหม่", address=None)


@app.route("/address/<int:address_id>/edit", methods=["GET", "POST"])
def edit_address(address_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    address = conn.execute("SELECT * FROM addresses WHERE id = ? AND user_id = ?", 
                           (address_id, user_id)).fetchone()

    if not address:
        flash("ไม่พบที่อยู่")
        return redirect(url_for("address_book"))

    if request.method == "POST":
        recipient_name = request.form["recipient_name"]
        phone = request.form["phone"]
        address = request.form["address"]
        city = request.form.get("city", "")
        postal_code = request.form.get("postal_code", "")
        province = request.form.get("province", "")

        conn = get_db_connection()
        conn.execute("""
            UPDATE addresses
            SET recipient_name = ?, phone = ?, address = ?, city = ?, postal_code = ?, province = ?
            WHERE id = ? AND user_id = ?
        """, (recipient_name, phone, address, city, postal_code, province, address_id, user_id))
        conn.commit()
        conn.close()

        flash("แก้ไขที่อยู่เรียบร้อยแล้ว")
        return redirect(url_for("address_book"))

    conn.close()
    return render_template("address_form.html", action="บันทึก", address=address)

@app.route("/address_book/delete/<int:address_id>", methods=["POST"])
def delete_address(address_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("กรุณาเข้าสู่ระบบก่อนใช้งาน")
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM addresses WHERE id=? AND user_id=?", (address_id, user_id)
    )
    conn.commit()
    conn.close()
    flash("ลบที่อยู่เรียบร้อยแล้ว")
    return redirect(url_for("address_book"))


@app.route("/track_order", methods=["GET", "POST"])
def track_order():
    user_id = session.get("user_id")
    role = session.get("role")

    if not user_id:
        flash("กรุณาเข้าสู่ระบบก่อน")
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        order_id = request.form.get("order_id")
        if order_id:
            if role == "admin":
                # admin เห็นได้ทุก order
                order = conn.execute(
                    "SELECT * FROM orders WHERE id=?",
                    (order_id,)
                ).fetchone()
            else:
                # user ปกติ เห็นเฉพาะของตัวเอง
                order = conn.execute(
                    "SELECT * FROM orders WHERE id=? AND user_id=?",
                    (order_id, user_id)
                ).fetchone()

            conn.close()
            if order:
                return redirect(url_for("order_detail", order_id=order["id"]))
            else:
                flash("ไม่พบคำสั่งซื้อ หรือคุณไม่มีสิทธิ์ดู")
                return redirect(url_for("track_order"))

    # ถ้าไม่ค้นหา ให้โชว์รายการล่าสุดแทน
    if role == "admin":
        all_orders = conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    else:
        all_orders = conn.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        ).fetchall()

    conn.close()
    return render_template("track_order.html", all_orders=all_orders)




@app.route('/get_cart_summary')
def get_cart_summary():
    total_items, total_price = get_cart_total()
    return jsonify({'success': True, 'total_items': total_items, 'total_price': total_price})

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value  # คืนค่าเดิมถ้าแปลงไม่ได้
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

# ========================
# Admin Delete Order API
# ========================

@app.route('/admin/delete_order/<int:order_id>', methods=['DELETE'])
def admin_delete_order(order_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์เข้าถึง'}), 403
    conn = get_db_connection()
    try:
        # ตรวจสอบว่ามี order นี้จริง
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'ไม่พบคำสั่งซื้อ'}), 404
        # ลบ order_items ก่อน
        conn.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
        # ลบ order หลัก
        conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 500
# ========================
# Initialize Application
# ========================

if __name__ == "__main__":
    print("Initializing Sweet Dreams Bakery...")
    init_db()
    print("Database initialized")
    seed_categories()
    print("Categories seeded")
    seed_products()
    print("Products seeded")
    create_admin_user()
    print("Admin user created")
    create_default_images_folder()
    print("Images folder created")
    print("\n" + "="*50)
    print("Sweet Dreams Bakery Server Starting...")
    print("="*50)
    print("Main Website: http://localhost:5000")
    print("Admin Panel: http://localhost:5000/admin")
    print("Manage Orders: http://localhost:5000/admin/orders")
    print("Admin Login: username=admin, password=admin123")
    print("="*50)
    print("Features Available:")
    print("   ✅ Product Management (Add/Edit/Delete)")
    print("   ✅ Order Management")
    print("   ✅ User Authentication")
    print("   ✅ Shopping Cart")
    print("   ✅ User Profiles")
    print("   ✅ Order History")
    print("   ✅ Responsive Design")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)