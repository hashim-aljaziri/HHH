from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import csv
import os

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)


def resolve_database_url():
    db_url = os.getenv('DATABASE_URL', '').strip()
    if db_url:
        # Some providers still expose postgres://, SQLAlchemy expects postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    return f"sqlite:///{os.path.join(INSTANCE_DIR, 'qurra.db')}"


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'qurra_dev_secret_change_me')
app.config['SQLALCHEMY_DATABASE_URI'] = resolve_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'svg'}
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true':
    app.config['SESSION_COOKIE_SECURE'] = True

if not os.path.isdir(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

THEMES = ['light', 'dark', 'pink', 'ocean', 'sand', 'forest']

ALLOWED_FONT_CHOICES = {
    'Playfair Display': 'Playfair Display',
    'Poppins': 'Poppins',
    'Montserrat': 'Montserrat',
    'Lora': 'Lora',
}

ALLOWED_ARABIC_FONT_CHOICES = {
    'Amiri': 'Amiri',
    'Cairo': 'Cairo',
    'Tajawal': 'Tajawal',
}

DEFAULT_TYPOGRAPHY = {
    'font_family_latin': 'Playfair Display',
    'font_family_arabic': 'Amiri',
    'font_scale_base': '1.00',
    'font_scale_heading': '1.00',
    'font_scale_nav': '1.00',
}

ADMIN_ROLE_PRESETS = {
    'owner': {
        'can_manage_settings': True,
        'can_manage_products': True,
        'can_manage_admins': True,
    },
    'manager': {
        'can_manage_settings': True,
        'can_manage_products': True,
        'can_manage_admins': False,
    },
    'editor': {
        'can_manage_settings': False,
        'can_manage_products': True,
        'can_manage_admins': False,
    },
}

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    fabric_type = db.Column(db.String(80))
    season = db.Column(db.String(20), default='summer')
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), default='logo.svg')
    stock_s = db.Column(db.Integer, default=5)
    stock_m = db.Column(db.Integer, default=5)
    stock_l = db.Column(db.Integer, default=5)
    is_available = db.Column(db.Boolean, default=True)
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255))

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    can_manage_settings = db.Column(db.Boolean, default=True)
    can_manage_products = db.Column(db.Boolean, default=True)
    can_manage_admins = db.Column(db.Boolean, default=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    tracking_code = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer)
    product_name_en = db.Column(db.String(100))
    product_name_ar = db.Column(db.String(100))
    size = db.Column(db.String(5))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

class CustomerSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)


def get_setting(key, default=None):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if not setting:
        setting = Setting(key=key)
    setting.value = value
    db.session.add(setting)
    db.session.commit()


def get_text(key, default=None):
    return get_setting(key, default)


def clamp_float(value, default, min_value=0.8, max_value=1.4):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_logo_options():
    path = app.config['UPLOAD_FOLDER']
    if not os.path.isdir(path):
        return []
    return sorted([f for f in os.listdir(path) if f.lower().endswith(tuple(app.config['ALLOWED_EXTENSIONS']))])


def ensure_product_schema_columns():
    """Backfill new product columns for existing SQLite databases."""
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(product)")).fetchall()
    }

    if 'fabric_type' not in columns:
        db.session.execute(text("ALTER TABLE product ADD COLUMN fabric_type VARCHAR(80)"))
    if 'season' not in columns:
        db.session.execute(text("ALTER TABLE product ADD COLUMN season VARCHAR(20) DEFAULT 'summer'"))
    if 'is_available' not in columns:
        db.session.execute(text("ALTER TABLE product ADD COLUMN is_available BOOLEAN DEFAULT 1"))
    db.session.execute(text("UPDATE product SET is_available = 1 WHERE is_available IS NULL"))

    db.session.commit()


def ensure_admin_schema_columns():
    """Backfill new admin permission columns for existing SQLite databases."""
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(admin_user)")).fetchall()
    }

    if 'can_manage_settings' not in columns:
        db.session.execute(text("ALTER TABLE admin_user ADD COLUMN can_manage_settings BOOLEAN DEFAULT 1"))
    if 'can_manage_products' not in columns:
        db.session.execute(text("ALTER TABLE admin_user ADD COLUMN can_manage_products BOOLEAN DEFAULT 1"))
    if 'can_manage_admins' not in columns:
        db.session.execute(text("ALTER TABLE admin_user ADD COLUMN can_manage_admins BOOLEAN DEFAULT 1"))

    db.session.commit()


def get_current_admin_user():
    username = session.get('admin_user', '').strip()
    if not username:
        return None
    return AdminUser.query.filter_by(username=username).first()


def resolve_admin_permissions(form_data, role_field='role_preset'):
    role_preset = (form_data.get(role_field, 'custom') or 'custom').strip().lower()
    if role_preset in ADMIN_ROLE_PRESETS:
        return ADMIN_ROLE_PRESETS[role_preset].copy()

    return {
        'can_manage_settings': form_data.get('can_manage_settings') == 'on',
        'can_manage_products': form_data.get('can_manage_products') == 'on',
        'can_manage_admins': form_data.get('can_manage_admins') == 'on',
    }


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_permission_required(permission_field):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            admin = get_current_admin_user()
            if not admin:
                session.pop('admin_user', None)
                return redirect(url_for('login', next=request.path))
            if not bool(getattr(admin, permission_field, False)):
                flash('You do not have permission for this action.', 'error')
                return redirect(url_for('control_panel'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

with app.app_context():
    db.create_all()
    ensure_product_schema_columns()
    ensure_admin_schema_columns()

    if AdminUser.query.count() == 0:
        admins = [
            ('admin1', 'QurraAdmin#1'),
            ('admin2', 'QurraAdmin#2'),
            ('admin3', 'QurraAdmin#3'),
        ]
        for username, password in admins:
            db.session.add(AdminUser(
                username=username,
                password_hash=generate_password_hash(password),
                can_manage_settings=True,
                can_manage_products=True,
                can_manage_admins=True,
            ))
        db.session.commit()

    if Setting.query.filter_by(key='default_theme').first() is None:
        set_setting('default_theme', 'light')
    if Setting.query.filter_by(key='site_logo').first() is None:
        set_setting('site_logo', 'logo.svg')
    if Setting.query.filter_by(key='site_background').first() is None:
        set_setting('site_background', 'logo-bg.svg')
    if Setting.query.filter_by(key='hero_title_en').first() is None:
        set_setting('hero_title_en', 'Timeless Libyan Grace')
    if Setting.query.filter_by(key='hero_title_ar').first() is None:
        set_setting('hero_title_ar', 'رقيّ العباءة الليبية')
    if Setting.query.filter_by(key='hero_subtitle_en').first() is None:
        set_setting('hero_subtitle_en', 'Premium fabrics tailored for the modern woman')
    if Setting.query.filter_by(key='hero_subtitle_ar').first() is None:
        set_setting('hero_subtitle_ar', 'أرقى الأقمشة مفصلة خصيصاً للمرأة العصرية')
    if Setting.query.filter_by(key='hero_button_text_en').first() is None:
        set_setting('hero_button_text_en', 'View Collection')
    if Setting.query.filter_by(key='hero_button_text_ar').first() is None:
        set_setting('hero_button_text_ar', 'تصفحي المجموعة')
    if Setting.query.filter_by(key='featured_title_en').first() is None:
        set_setting('featured_title_en', 'Curated Selection')
    if Setting.query.filter_by(key='featured_title_ar').first() is None:
        set_setting('featured_title_ar', 'مختاراتنا لكِ')
    if Setting.query.filter_by(key='featured_description_en').first() is None:
        set_setting('featured_description_en', 'A selection of styles crafted for your elegance.')
    if Setting.query.filter_by(key='featured_description_ar').first() is None:
        set_setting('featured_description_ar', 'مجموعة من التصاميم المصممة لأناقتك.')
    for setting_key, setting_value in DEFAULT_TYPOGRAPHY.items():
        if Setting.query.filter_by(key=setting_key).first() is None:
            set_setting(setting_key, setting_value)

    if Product.query.count() == 0:
        sample_products = [
            Product(
                name_ar='عباية ملكية',
                name_en='Royal Abaya',
                category='Silk',
                fabric_type='Silk',
                season='winter',
                price=240.0,
                image='logo.svg',
                stock_s=5,
                stock_m=5,
                stock_l=5,
                description_ar='عباية فاخرة مصنوعة من الحرير مع لمسات ذهبية.',
                description_en='A luxurious silk abaya with gold accents.'
            ),
            Product(
                name_ar='جلابية فاخرة',
                name_en='Luxury Jalabiya',
                category='Velvet',
                fabric_type='Velvet',
                season='winter',
                price=190.0,
                image='logo.svg',
                stock_s=4,
                stock_m=6,
                stock_l=3,
                description_ar='جلابية مطرزة يدوياً بتصميم شرقي أنيق.',
                description_en='A hand-embroidered jalabiya with elegant Eastern styling.'
            ),
            Product(
                name_ar='عباءة كلاسيكية',
                name_en='Classic Abaya',
                category='Cotton',
                fabric_type='Cotton',
                season='summer',
                price=130.0,
                image='logo.svg',
                stock_s=6,
                stock_m=8,
                stock_l=5,
                description_ar='تصميم عملي ومريح يناسب جميع المناسبات.',
                description_en='A practical, comfortable design suitable for every occasion.'
            ),
            Product(
                name_ar='عباية تراثية',
                name_en='Heritage Abaya',
                category='Linen',
                fabric_type='Linen',
                season='summer',
                price=170.0,
                image='logo.svg',
                stock_s=7,
                stock_m=6,
                stock_l=4,
                description_ar='عباية بلمسة تراثية أنيقة مناسبة للإطلالات اليومية.',
                description_en='A heritage-inspired abaya with an elegant everyday look.'
            )
        ]
        db.session.add_all(sample_products)
        db.session.commit()

    if Product.query.filter_by(name_en='Heritage Abaya').first() is None:
        db.session.add(Product(
            name_ar='عباية تراثية',
            name_en='Heritage Abaya',
            category='Linen',
            fabric_type='Linen',
            season='summer',
            price=170.0,
            image='logo.svg',
            stock_s=7,
            stock_m=6,
            stock_l=4,
            description_ar='عباية بلمسة تراثية أنيقة مناسبة للإطلالات اليومية.',
            description_en='A heritage-inspired abaya with an elegant everyday look.'
        ))
        db.session.commit()

@app.before_request
def set_defaults():
    if 'lang' not in session:
        session['lang'] = 'ar'
    if 'theme' not in session:
        session['theme'] = get_setting('default_theme', 'light')
    if 'customer_session' not in session:
        session['customer_session'] = os.urandom(24).hex()
    if 'customer_id' in session:
        customer_session = CustomerSession.query.filter_by(session_token=session['customer_session']).first()
        if not customer_session:
            customer_session = CustomerSession(
                customer_id=session['customer_id'],
                session_token=session['customer_session']
            )
            db.session.add(customer_session)
        else:
            customer_session.customer_id = session['customer_id']
        customer_session.last_seen = datetime.utcnow()
        db.session.commit()

@app.context_processor
def inject_globals():
    lang = session.get('lang', 'ar')
    current_customer = None
    cart = session.get('cart', {})
    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    customer_id = session.get('customer_id')
    if customer_id:
        current_customer = Customer.query.get(customer_id)
    active_customer_count = CustomerSession.query.filter(CustomerSession.last_seen >= datetime.utcnow() - timedelta(minutes=30)).count()
    return {
        'lang': lang,
        'theme': session.get('theme', get_setting('default_theme', 'light')),
        'themes': THEMES,
        'admin_user': session.get('admin_user'),
        'customer_user': current_customer,
        'customer_count': Customer.query.count(),
        'online_customers': active_customer_count,
        'cart_count': cart_count,
        'logo': get_setting('site_logo', 'logo.svg'),
        'background_logo': get_setting('site_background', 'logo-bg.svg'),
        'hero_title': get_text(f'hero_title_{lang}', 'رقيّ العباءة الليبية' if lang == 'ar' else 'Timeless Libyan Grace'),
        'hero_subtitle': get_text(f'hero_subtitle_{lang}', 'أرقى الأقمشة مفصلة خصيصاً للمرأة العصرية' if lang == 'ar' else 'Premium fabrics tailored for the modern woman'),
        'hero_button_text': get_text(f'hero_button_text_{lang}', 'تصفحي المجموعة' if lang == 'ar' else 'View Collection'),
        'featured_title': get_text(f'featured_title_{lang}', 'مختاراتنا لكِ' if lang == 'ar' else 'Curated Selection'),
        'featured_description': get_text(f'featured_description_{lang}', 'مجموعة من التصاميم مصممة لأناقتك.' if lang == 'ar' else 'A selection of styles crafted for your elegance.'),
        'font_family_latin': get_setting('font_family_latin', 'Playfair Display'),
        'font_family_arabic': get_setting('font_family_arabic', 'Amiri'),
        'font_scale_base': clamp_float(get_setting('font_scale_base', '1.00'), 1.0),
        'font_scale_heading': clamp_float(get_setting('font_scale_heading', '1.00'), 1.0),
        'font_scale_nav': clamp_float(get_setting('font_scale_nav', '1.00'), 1.0),
    }

@app.route('/')
def index():
    products = Product.query.filter_by(is_available=True).limit(4).all()
    return render_template('index.html', lang=session['lang'], products=products)

@app.route('/shop')
def shop():
    products = Product.query.filter_by(is_available=True).all()
    return render_template('shop.html', lang=session['lang'], products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', lang=session['lang'], product=product)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = AdminUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['admin_user'] = user.username
            flash('Welcome back, {}!'.format(user.username), 'success')
            return redirect(url_for('control_panel'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', lang=session['lang'])

@app.route('/logout')
def logout():
    session.pop('admin_user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        customer = Customer.query.filter_by(email=email).first()
        if customer and check_password_hash(customer.password_hash, password):
            session['customer_id'] = customer.id
            flash('Welcome back, {}!'.format(customer.username), 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'error')
    return render_template('customer_login.html', lang=session['lang'])

@app.route('/customer/register', methods=['POST'])
def customer_register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    if not username or not email or not password:
        flash('Please complete all registration fields.', 'error')
        return redirect(url_for('customer_login'))
    if Customer.query.filter((Customer.email == email) | (Customer.username == username)).first():
        flash('Email or username is already in use.', 'error')
        return redirect(url_for('customer_login'))
    customer = Customer(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(customer)
    db.session.commit()
    session['customer_id'] = customer.id
    flash('Account created successfully. You are now logged in.', 'success')
    return redirect(url_for('index'))

@app.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    flash('Customer session ended.', 'info')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_available:
        flash('This product is currently unavailable.', 'error')
        return redirect(request.referrer or url_for('shop'))

    size = request.form.get('size', 'M')
    quantity = int(request.form.get('quantity', 1) or 1)
    cart = session.get('cart', {})
    key = f'{product_id}:{size}'
    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'product_id': product.id,
            'product_name_en': product.name_en,
            'product_name_ar': product.name_ar,
            'price': product.price,
            'size': size,
            'quantity': quantity,
            'image': product.image,
        }
    session['cart'] = cart
    flash('Added item to cart.', 'success')
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', lang=session['lang'], cart=cart, subtotal=subtotal)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', {})
    for key, item in list(cart.items()):
        quantity = int(request.form.get(f'quantity_{key}', item['quantity']) or 0)
        if quantity <= 0:
            cart.pop(key, None)
        else:
            cart[key]['quantity'] = quantity
    session['cart'] = cart
    flash('Cart updated.', 'success')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'customer_id' not in session:
        flash('Please login or register to place your order.', 'error')
        return redirect(url_for('customer_login'))
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('shop'))
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
    order = Order(customer_id=session['customer_id'], total_amount=total_amount, tracking_code='pending')
    db.session.add(order)
    db.session.commit()
    order.tracking_code = f'QURRA{order.id}{os.urandom(3).hex().upper()}'
    for item in cart.values():
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product_id'],
            product_name_en=item['product_name_en'],
            product_name_ar=item['product_name_ar'],
            size=item['size'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
        db.session.add(Sale(product_id=item['product_id'], amount=item['price'] * item['quantity']))
    db.session.commit()
    session.pop('cart', None)
    flash('Order placed successfully! Your tracking code is {}'.format(order.tracking_code), 'success')
    return redirect(url_for('customer_orders'))

@app.route('/orders')
def customer_orders():
    if 'customer_id' not in session:
        flash('Please login to view your orders.', 'error')
        return redirect(url_for('customer_login'))
    orders = Order.query.filter_by(customer_id=session['customer_id']).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', lang=session['lang'], orders=orders)

@app.route('/track', methods=['GET'])
def track_order():
    tracking_code = request.args.get('code', '').strip()
    order = None
    if tracking_code:
        order = Order.query.filter_by(tracking_code=tracking_code).first()
        if not order:
            flash('No order found with that tracking code.', 'error')
    return render_template('track.html', lang=session['lang'], order=order, tracking_code=tracking_code)


def get_inventory_stats():
    """Get inventory statistics for all products."""
    products = Product.query.all()
    total_stock = 0
    low_stock_items = []
    stock_by_size = {'S': 0, 'M': 0, 'L': 0}
    
    for p in products:
        total_stock += p.stock_s + p.stock_m + p.stock_l
        stock_by_size['S'] += p.stock_s
        stock_by_size['M'] += p.stock_m
        stock_by_size['L'] += p.stock_l
        if (p.stock_s + p.stock_m + p.stock_l) < 5:
            low_stock_items.append({
                'name': p.name_en,
                'stock': p.stock_s + p.stock_m + p.stock_l
            })
    
    return {
        'total_stock': total_stock,
        'total_products': len(products),
        'low_stock_items': low_stock_items,
        'stock_by_size': stock_by_size,
        'products': products
    }


def get_finance_stats():
    """Get comprehensive finance and sales statistics."""
    sales = Sale.query.all()
    products = Product.query.all()
    
    total_earnings = sum(s.amount for s in sales) if sales else 0
    total_sales = len(sales)
    avg_order = total_earnings / total_sales if total_sales > 0 else 0
    
    # Revenue by product
    revenue_by_product = {}
    for p in products:
        p_sales = [s for s in sales if s.product_id == p.id]
        if p_sales:
            revenue_by_product[p.name_en] = sum(s.amount for s in p_sales)
    
    # Top sellers
    top_sellers = sorted(revenue_by_product.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total_earnings': round(total_earnings, 2),
        'total_sales': total_sales,
        'avg_order_value': round(avg_order, 2),
        'revenue_by_product': revenue_by_product,
        'top_sellers': top_sellers
    }


@app.route('/control', methods=['GET', 'POST'])
@admin_required
def control_panel():
    current_admin = get_current_admin_user()
    if not current_admin:
        session.pop('admin_user', None)
        flash('Admin session was not found. Please log in again.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if not current_admin.can_manage_settings:
            flash('You do not have permission to update site settings.', 'error')
            return redirect(url_for('control_panel'))

        if request.form.get('action') == 'reset_typography':
            for setting_key, setting_value in DEFAULT_TYPOGRAPHY.items():
                set_setting(setting_key, setting_value)
            flash('Typography settings have been reset to default.', 'success')
            return redirect(url_for('control_panel'))

        selected_theme = request.form.get('default_theme', 'light')
        selected_logo = request.form.get('site_logo', 'logo.svg')
        selected_background = request.form.get('site_background', 'logo-bg.svg')
        if selected_theme in THEMES:
            set_setting('default_theme', selected_theme)
            session['theme'] = selected_theme
        if selected_logo in get_logo_options():
            set_setting('site_logo', selected_logo)
        if selected_background in get_logo_options():
            set_setting('site_background', selected_background)

        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename and allowed_file(logo_file.filename):
            filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('site_logo', filename)

        background_file = request.files.get('background_logo_file')
        if background_file and background_file.filename and allowed_file(background_file.filename):
            filename = secure_filename(background_file.filename)
            background_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('site_background', filename)

        set_setting('hero_title_en', request.form.get('hero_title_en', '').strip() or get_setting('hero_title_en'))
        set_setting('hero_title_ar', request.form.get('hero_title_ar', '').strip() or get_setting('hero_title_ar'))
        set_setting('hero_subtitle_en', request.form.get('hero_subtitle_en', '').strip() or get_setting('hero_subtitle_en'))
        set_setting('hero_subtitle_ar', request.form.get('hero_subtitle_ar', '').strip() or get_setting('hero_subtitle_ar'))
        set_setting('hero_button_text_en', request.form.get('hero_button_text_en', '').strip() or get_setting('hero_button_text_en'))
        set_setting('hero_button_text_ar', request.form.get('hero_button_text_ar', '').strip() or get_setting('hero_button_text_ar'))
        set_setting('featured_title_en', request.form.get('featured_title_en', '').strip() or get_setting('featured_title_en'))
        set_setting('featured_title_ar', request.form.get('featured_title_ar', '').strip() or get_setting('featured_title_ar'))
        set_setting('featured_description_en', request.form.get('featured_description_en', '').strip() or get_setting('featured_description_en'))
        set_setting('featured_description_ar', request.form.get('featured_description_ar', '').strip() or get_setting('featured_description_ar'))

        latin_font = request.form.get('font_family_latin', DEFAULT_TYPOGRAPHY['font_family_latin']).strip()
        arabic_font = request.form.get('font_family_arabic', DEFAULT_TYPOGRAPHY['font_family_arabic']).strip()
        base_scale = clamp_float(request.form.get('font_scale_base', DEFAULT_TYPOGRAPHY['font_scale_base']), 1.0)
        heading_scale = clamp_float(request.form.get('font_scale_heading', DEFAULT_TYPOGRAPHY['font_scale_heading']), 1.0)
        nav_scale = clamp_float(request.form.get('font_scale_nav', DEFAULT_TYPOGRAPHY['font_scale_nav']), 1.0)

        set_setting('font_family_latin', ALLOWED_FONT_CHOICES.get(latin_font, DEFAULT_TYPOGRAPHY['font_family_latin']))
        set_setting('font_family_arabic', ALLOWED_ARABIC_FONT_CHOICES.get(arabic_font, DEFAULT_TYPOGRAPHY['font_family_arabic']))
        set_setting('font_scale_base', f'{base_scale:.2f}')
        set_setting('font_scale_heading', f'{heading_scale:.2f}')
        set_setting('font_scale_nav', f'{nav_scale:.2f}')

        flash('Control panel settings have been updated.', 'success')
        return redirect(url_for('control_panel'))

    logos = get_logo_options()
    current_theme = get_setting('default_theme', 'light')
    current_logo = get_setting('site_logo', 'logo.svg')
    current_background = get_setting('site_background', 'logo-bg.svg')
    admin_users = AdminUser.query.order_by(AdminUser.id.asc()).all()
    
    # Get analytics data
    inventory_stats = get_inventory_stats()
    finance_stats = get_finance_stats()
    products = Product.query.order_by(Product.id.desc()).all()
    
    return render_template(
        'control_panel.html',
        lang=session['lang'],
        themes=THEMES,
        current_admin=current_admin,
        logos=logos,
        current_theme=current_theme,
        current_logo=current_logo,
        current_background=current_background,
        admin_users=admin_users,
        hero_title_en=get_text('hero_title_en', 'Timeless Libyan Grace'),
        hero_title_ar=get_text('hero_title_ar', 'رقيّ العباءة الليبية'),
        hero_subtitle_en=get_text('hero_subtitle_en', 'Premium fabrics tailored for the modern woman'),
        hero_subtitle_ar=get_text('hero_subtitle_ar', 'أرقى الأقمشة مفصلة خصيصاً للمرأة العصرية'),
        hero_button_text_en=get_text('hero_button_text_en', 'View Collection'),
        hero_button_text_ar=get_text('hero_button_text_ar', 'تصفحي المجموعة'),
        featured_title_en=get_text('featured_title_en', 'Curated Selection'),
        featured_title_ar=get_text('featured_title_ar', 'مختاراتنا لكِ'),
        featured_description_en=get_text('featured_description_en', 'A selection of styles crafted for your elegance.'),
        featured_description_ar=get_text('featured_description_ar', 'مجموعة من التصاميم المصممة لأناقتك.'),
        font_family_latin=get_setting('font_family_latin', DEFAULT_TYPOGRAPHY['font_family_latin']),
        font_family_arabic=get_setting('font_family_arabic', DEFAULT_TYPOGRAPHY['font_family_arabic']),
        font_scale_base=get_setting('font_scale_base', DEFAULT_TYPOGRAPHY['font_scale_base']),
        font_scale_heading=get_setting('font_scale_heading', DEFAULT_TYPOGRAPHY['font_scale_heading']),
        font_scale_nav=get_setting('font_scale_nav', DEFAULT_TYPOGRAPHY['font_scale_nav']),
        allowed_font_choices=sorted(ALLOWED_FONT_CHOICES.keys()),
        allowed_arabic_font_choices=sorted(ALLOWED_ARABIC_FONT_CHOICES.keys()),
        products=products,
        inventory_stats=inventory_stats,
        finance_stats=finance_stats
    )


@app.route('/control/admin/password', methods=['POST'])
@admin_required
def control_update_admin_password():
    username = session.get('admin_user', '').strip()
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    admin = AdminUser.query.filter_by(username=username).first()
    if not admin:
        session.pop('admin_user', None)
        flash('Admin session was not found. Please log in again.', 'error')
        return redirect(url_for('login'))

    if not check_password_hash(admin.password_hash, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('control_panel'))

    if len(new_password) < 8:
        flash('New password must be at least 8 characters.', 'error')
        return redirect(url_for('control_panel'))

    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'error')
        return redirect(url_for('control_panel'))

    admin.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Admin password updated successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/admins/add', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_admins')
def control_add_admin_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username:
        flash('Admin username is required.', 'error')
        return redirect(url_for('control_panel'))

    if len(password) < 8:
        flash('Admin password must be at least 8 characters.', 'error')
        return redirect(url_for('control_panel'))

    if AdminUser.query.filter_by(username=username).first():
        flash('This admin username already exists.', 'error')
        return redirect(url_for('control_panel'))

    permissions = resolve_admin_permissions(request.form)

    admin = AdminUser(
        username=username,
        password_hash=generate_password_hash(password),
        can_manage_settings=permissions['can_manage_settings'],
        can_manage_products=permissions['can_manage_products'],
        can_manage_admins=permissions['can_manage_admins'],
    )
    db.session.add(admin)
    db.session.commit()
    flash('Admin user added successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/admins/update/<int:id>', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_admins')
def control_update_admin_user(id):
    current_admin = get_current_admin_user()
    admin = AdminUser.query.get_or_404(id)

    username = request.form.get('username', '').strip()
    if not username:
        flash('Admin username is required.', 'error')
        return redirect(url_for('control_panel'))

    existing = AdminUser.query.filter_by(username=username).first()
    if existing and existing.id != admin.id:
        flash('This admin username is already used by another account.', 'error')
        return redirect(url_for('control_panel'))

    permissions = resolve_admin_permissions(request.form)
    can_manage_settings = permissions['can_manage_settings']
    can_manage_products = permissions['can_manage_products']
    can_manage_admins = permissions['can_manage_admins']

    manage_admins_count = AdminUser.query.filter_by(can_manage_admins=True).count()
    is_last_manage_admin = admin.can_manage_admins and manage_admins_count <= 1

    if is_last_manage_admin and not can_manage_admins:
        flash('At least one admin must keep Admin Management permission.', 'error')
        return redirect(url_for('control_panel'))

    if current_admin and admin.id == current_admin.id and not can_manage_admins:
        flash('You cannot remove your own Admin Management permission.', 'error')
        return redirect(url_for('control_panel'))

    admin.username = username
    admin.can_manage_settings = can_manage_settings
    admin.can_manage_products = can_manage_products
    admin.can_manage_admins = can_manage_admins

    new_password = request.form.get('new_password', '').strip()
    if new_password:
        if len(new_password) < 8:
            flash('New admin password must be at least 8 characters.', 'error')
            return redirect(url_for('control_panel'))
        admin.password_hash = generate_password_hash(new_password)

    db.session.commit()

    if current_admin and admin.id == current_admin.id:
        session['admin_user'] = admin.username

    flash('Admin user updated successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/admins/delete/<int:id>', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_admins')
def control_delete_admin_user(id):
    current_admin = get_current_admin_user()
    admin = AdminUser.query.get(id)
    if not admin:
        flash('Admin user was not found.', 'error')
        return redirect(url_for('control_panel'))

    if current_admin and admin.id == current_admin.id:
        flash('You cannot delete your own active admin account.', 'error')
        return redirect(url_for('control_panel'))

    if AdminUser.query.count() <= 1:
        flash('At least one admin account must exist.', 'error')
        return redirect(url_for('control_panel'))

    manage_admins_count = AdminUser.query.filter_by(can_manage_admins=True).count()
    if admin.can_manage_admins and manage_admins_count <= 1:
        flash('Cannot delete the last admin with Admin Management permission.', 'error')
        return redirect(url_for('control_panel'))

    db.session.delete(admin)
    db.session.commit()
    flash('Admin user deleted successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/products/add', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_products')
def control_add_product():
    name_ar = request.form.get('name_ar', '').strip()
    name_en = request.form.get('name_en', '').strip()
    category = request.form.get('category', '').strip()
    fabric_type = request.form.get('fabric_type', '').strip()
    season = request.form.get('season', 'summer').strip().lower()
    description_ar = request.form.get('desc_ar', '').strip()
    description_en = request.form.get('desc_en', '').strip()

    if season not in {'summer', 'winter'}:
        season = 'summer'

    if not name_ar or not name_en:
        flash('Arabic and English names are required.', 'error')
        return redirect(url_for('control_panel'))

    try:
        price = float(request.form.get('price', '0').strip())
    except ValueError:
        flash('Price must be a valid number.', 'error')
        return redirect(url_for('control_panel'))

    def parse_stock(field):
        try:
            return max(0, int(request.form.get(field, '0').strip() or 0))
        except ValueError:
            return 0

    stock_s = parse_stock('stock_s')
    stock_m = parse_stock('stock_m')
    stock_l = parse_stock('stock_l')
    is_available = request.form.get('is_available') == 'on'

    image_filename = request.form.get('image', 'logo.svg').strip() or 'logo.svg'
    if image_filename not in get_logo_options():
        image_filename = 'logo.svg'

    product_image_file = request.files.get('product_image_file')
    if product_image_file and product_image_file.filename and allowed_file(product_image_file.filename):
        filename = secure_filename(product_image_file.filename)
        product_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_filename = filename

    db.session.add(Product(
        name_ar=name_ar,
        name_en=name_en,
        category=category,
        fabric_type=fabric_type,
        season=season,
        price=price,
        image=image_filename,
        stock_s=stock_s,
        stock_m=stock_m,
        stock_l=stock_l,
        is_available=is_available,
        description_ar=description_ar,
        description_en=description_en
    ))
    db.session.commit()
    flash('Product added successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/products/update/<int:id>', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_products')
def control_update_product(id):
    product = Product.query.get_or_404(id)

    product.name_ar = request.form.get('name_ar', '').strip() or product.name_ar
    product.name_en = request.form.get('name_en', '').strip() or product.name_en
    product.category = request.form.get('category', '').strip()
    product.fabric_type = request.form.get('fabric_type', '').strip()
    selected_season = request.form.get('season', product.season or 'summer').strip().lower()
    product.season = selected_season if selected_season in {'summer', 'winter'} else 'summer'
    product.description_ar = request.form.get('desc_ar', '').strip()
    product.description_en = request.form.get('desc_en', '').strip()

    try:
        product.price = float(request.form.get('price', str(product.price)).strip())
    except ValueError:
        flash('Price must be a valid number.', 'error')
        return redirect(url_for('control_panel'))

    def parse_stock(field, current):
        try:
            return max(0, int(request.form.get(field, str(current)).strip() or current))
        except ValueError:
            return current

    product.stock_s = parse_stock('stock_s', product.stock_s)
    product.stock_m = parse_stock('stock_m', product.stock_m)
    product.stock_l = parse_stock('stock_l', product.stock_l)
    product.is_available = request.form.get('is_available') == 'on'

    selected_image = request.form.get('image', product.image).strip() or product.image
    if selected_image in get_logo_options():
        product.image = selected_image

    if request.form.get('reset_image') == 'on':
        product.image = 'logo.svg'

    product_image_file = request.files.get('product_image_file')
    if product_image_file and product_image_file.filename and allowed_file(product_image_file.filename):
        filename = secure_filename(product_image_file.filename)
        product_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        product.image = filename

    db.session.commit()
    flash('Product updated successfully.', 'success')
    return redirect(url_for('control_panel'))


@app.route('/control/products/delete/<int:id>', methods=['POST'])
@admin_required
@admin_permission_required('can_manage_products')
def control_delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.', 'success')
    return redirect(url_for('control_panel'))

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
@admin_permission_required('can_manage_products')
def admin():
    if request.method == 'POST':
        csv_file = request.files.get('product_csv')
        if csv_file and csv_file.filename.lower().endswith('.csv'):
            decoded = csv_file.stream.read().decode('utf-8-sig')
            reader = csv.DictReader(decoded.splitlines())
            imported = 0
            for row in reader:
                if not row.get('name_en') or not row.get('name_ar') or not row.get('price'):
                    continue
                image_filename = row.get('image', '').strip() or 'logo.svg'
                if image_filename and allowed_file(image_filename):
                    # use image filename only; actual image file should be uploaded separately or already exist.
                    image_filename = secure_filename(image_filename)
                else:
                    image_filename = 'logo.svg'
                try:
                    price = float(row.get('price', 0))
                except ValueError:
                    price = 0.0
                try:
                    stock_s = int(row.get('stock_s', 0) or 0)
                except ValueError:
                    stock_s = 0
                try:
                    stock_m = int(row.get('stock_m', 0) or 0)
                except ValueError:
                    stock_m = 0
                try:
                    stock_l = int(row.get('stock_l', 0) or 0)
                except ValueError:
                    stock_l = 0
                product = Product(
                    name_ar=row.get('name_ar', '').strip(),
                    name_en=row.get('name_en', '').strip(),
                    category=row.get('category', '').strip(),
                    fabric_type=row.get('fabric_type', '').strip(),
                    season=(row.get('season', 'summer').strip().lower() if row.get('season') else 'summer'),
                    price=price,
                    image=image_filename,
                    stock_s=stock_s,
                    stock_m=stock_m,
                    stock_l=stock_l,
                    description_ar=row.get('desc_ar', '').strip(),
                    description_en=row.get('desc_en', '').strip()
                )
                db.session.add(product)
                imported += 1
            db.session.commit()
            flash(f'{imported} products imported from CSV.', 'success')
            return redirect(url_for('admin'))

        image_filename = request.form.get('image', 'logo.svg')
        product_image_file = request.files.get('product_image_file')
        if product_image_file and product_image_file.filename and allowed_file(product_image_file.filename):
            filename = secure_filename(product_image_file.filename)
            product_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        new_p = Product(
            name_ar=request.form['name_ar'],
            name_en=request.form['name_en'],
            category=request.form['category'],
            fabric_type=request.form.get('fabric_type', '').strip(),
            season=(request.form.get('season', 'summer').strip().lower() if request.form.get('season') else 'summer'),
            price=float(request.form['price']),
            image=image_filename,
            stock_s=int(request.form['stock_s']),
            stock_m=int(request.form['stock_m']),
            stock_l=int(request.form['stock_l']),
            description_ar=request.form['desc_ar'],
            description_en=request.form['desc_en']
        )
        db.session.add(new_p)
        db.session.commit()
        return redirect(url_for('admin'))
    
    products = Product.query.all()
    total_earnings = db.session.query(db.func.sum(Sale.amount)).scalar() or 0
    return render_template('admin.html', lang=session['lang'], products=products, earnings=total_earnings)

@app.route('/admin/delete/<int:id>')
@admin_required
@admin_permission_required('can_manage_products')
def delete_product(id):
    p = Product.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/switch_lang')
def switch_lang():
    session['lang'] = 'en' if session['lang'] == 'ar' else 'ar'
    return redirect(request.referrer or url_for('index'))

@app.route('/switch_theme/<theme>')
def switch_theme(theme):
    if theme not in THEMES:
        theme = 'light'
    session['theme'] = theme
    return redirect(request.referrer or url_for('index'))


@app.route('/health')
def health_check():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
