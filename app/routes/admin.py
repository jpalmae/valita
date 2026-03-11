from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.product import Product
from models.order_item import OrderItem
from extensions import db
import bcrypt
from utils.decorators import admin_required
import os
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

from sqlalchemy import func
from datetime import datetime

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    from models.order import Order, OrderStatus
    today = datetime.now().date()
    orders_today = Order.query.filter(db.func.date(Order.created_at) == today).count()
    
    first_day_month = today.replace(day=1)
    revenue_month_result = db.session.query(func.sum(Order.total)).filter(
        db.func.date(Order.created_at) >= first_day_month,
        Order.payment_status == 'approved'
    ).scalar()
    revenue_month = revenue_month_result or 0
    
    pending_orders = Order.query.filter_by(status=OrderStatus.RECIBIDO).count()
    manufacturing_orders = Order.query.filter_by(status=OrderStatus.EN_FABRICACION).count()
    
    latest_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                          orders_today=orders_today,
                          revenue_month=revenue_month,
                          pending_orders=pending_orders,
                          manufacturing_orders=manufacturing_orders,
                          latest_orders=latest_orders)

@admin_bp.route('/pedidos')
@login_required
@admin_required
def orders():
    from models.order import Order, OrderStatus

    current_status = request.args.get('status')
    query = Order.query.order_by(Order.created_at.desc())

    if current_status:
        try:
            query = query.filter_by(status=OrderStatus(current_status))
        except ValueError:
            flash('Estado de pedido no valido.', 'warning')
            return redirect(url_for('admin.orders'))

    order_list = query.all()
    return render_template(
        'admin/orders.html',
        orders=order_list,
        current_status=current_status,
        OrderStatus=OrderStatus,
    )

@admin_bp.route('/pedidos/<int:id>')
@login_required
@admin_required
def order_detail(id):
    from models.order import Order, OrderStatus

    order = Order.query.get_or_404(id)
    return render_template(
        'admin/order_detail.html',
        order=order,
        OrderStatus=OrderStatus,
    )

@admin_bp.route('/pedidos/<int:id>/estado', methods=['POST'])
@login_required
@admin_required
def order_status(id):
    from models.order import Order, OrderStatus

    order = Order.query.get_or_404(id)
    status_value = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '').strip() or None

    try:
        order.status = OrderStatus(status_value)
    except ValueError:
        flash('Estado de pedido no valido.', 'danger')
        return redirect(url_for('admin.order_detail', id=order.id))

    order.admin_notes = admin_notes
    db.session.commit()
    flash('Pedido actualizado correctamente.', 'success')
    return redirect(url_for('admin.order_detail', id=order.id))

# --- Product CRUD ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        return f"{filename}"
    return None

@admin_bp.route('/productos')
@login_required
@admin_required
def products():
    product_list = Product.query.order_by(Product.created_at.desc()).all()
    linked_product_ids = {
        product_id
        for (product_id,) in db.session.query(OrderItem.product_id).distinct().all()
    }
    return render_template(
        'admin/products.html',
        products=product_list,
        linked_product_ids=linked_product_ids,
    )

@admin_bp.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def product_new():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        weight_grams = request.form.get('weight_grams')
        is_active = request.form.get('is_active') == 'on'
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_url = save_image(file)
                if not image_url:
                    flash('Formato de imagen no permitido.', 'danger')
                    return redirect(request.url)
        
        product = Product(
            name=name, category=category, description=description,
            price=price, stock=stock, weight_grams=weight_grams or None,
            is_active=is_active, image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        flash('Producto creado exitosamente.', 'success')
        return redirect(url_for('admin.products'))
        
    return render_template('admin/product_form.html', product=None)

@admin_bp.route('/productos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.stock = request.form.get('stock')
        product.weight_grams = request.form.get('weight_grams') or None
        product.is_active = request.form.get('is_active') == 'on'
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                new_image_url = save_image(file)
                if new_image_url:
                    # Opcional: eliminar la imagen anterior
                    product.image_url = new_image_url
                else:
                    flash('Formato de imagen no permitido.', 'danger')
                    return redirect(request.url)
                    
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('admin.products'))
        
    return render_template('admin/product_form.html', product=product)

@admin_bp.route('/productos/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def product_toggle(id):
    product = Product.query.get_or_404(id)
    product.is_active = not product.is_active
    db.session.commit()
    flash(f"Producto '{product.name}' {'activado' if product.is_active else 'desactivado'}.", 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/productos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def product_delete(id):
    product = Product.query.get_or_404(id)

    if OrderItem.query.filter_by(product_id=product.id).first():
        flash(
            f"No se puede eliminar '{product.name}' porque ya esta asociado a pedidos. Desactivalo en su lugar.",
            'warning',
        )
        return redirect(url_for('admin.products'))

    if product.image_url:
        image_path = os.path.join(current_app.root_path, 'static', 'uploads', product.image_url)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product)
    db.session.commit()
    flash(f"Producto '{product.name}' eliminado correctamente.", 'success')
    return redirect(url_for('admin.products'))
