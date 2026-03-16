from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.product import Product
from models.order_item import OrderItem
from extensions import db, limiter
import bcrypt
from utils.decorators import admin_required
import os
import uuid
from PIL import Image
from sqlalchemy import func, or_
from datetime import date, timedelta
from utils.datetime import local_now, local_date_range_utc, local_date_to_utc_start, to_local

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

def _parse_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _append_order_status_history(order, new_status, note=None):
    from models.order import OrderStatusHistory

    if order.status == new_status:
        return False

    history_entry = OrderStatusHistory(
        order=order,
        previous_status=order.status,
        new_status=new_status,
        note=note,
        changed_by=current_user.email,
    )
    db.session.add(history_entry)
    order.status = new_status
    return True

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    from models.order import Order, OrderStatus

    today = local_now().date()
    start_week = today - timedelta(days=today.weekday())
    today_start_utc, today_end_utc = local_date_range_utc(today)
    week_start_utc = local_date_to_utc_start(start_week)
    month_start_utc = local_date_to_utc_start(today.replace(day=1))
    tomorrow_start_utc = today_end_utc

    orders_today = Order.query.filter(
        Order.created_at >= today_start_utc,
        Order.created_at < today_end_utc,
    ).count()
    orders_week = Order.query.filter(Order.created_at >= week_start_utc).count()

    orders_month = Order.query.filter(Order.created_at >= month_start_utc).count()
    revenue_month_result = db.session.query(func.sum(Order.total)).filter(
        Order.created_at >= month_start_utc,
        Order.payment_status == 'approved'
    ).scalar()
    revenue_month = revenue_month_result or 0

    pending_orders = Order.query.filter_by(status=OrderStatus.RECIBIDO).count()
    manufacturing_orders = Order.query.filter_by(status=OrderStatus.EN_FABRICACION).count()

    chart_start = today - timedelta(days=29)
    chart_start_utc = local_date_to_utc_start(chart_start)
    recent_orders = (
        Order.query
        .filter(Order.created_at >= chart_start_utc, Order.created_at < tomorrow_start_utc)
        .all()
    )
    counts_by_day = {}
    for order in recent_orders:
        local_day = to_local(order.created_at).date().isoformat()
        counts_by_day[local_day] = counts_by_day.get(local_day, 0) + 1
    chart_labels = []
    chart_values = []
    for offset in range(30):
        current_day = chart_start + timedelta(days=offset)
        chart_labels.append(current_day.strftime('%d/%m'))
        chart_values.append(counts_by_day.get(current_day.isoformat(), 0))

    latest_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        orders_today=orders_today,
        orders_week=orders_week,
        orders_month=orders_month,
        revenue_month=revenue_month,
        pending_orders=pending_orders,
        manufacturing_orders=manufacturing_orders,
        latest_orders=latest_orders,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )

@admin_bp.route('/pedidos')
@login_required
@admin_required
def orders():
    from models.order import Order, OrderStatus

    current_status = request.args.get('status')
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Order.query

    if current_status:
        try:
            query = query.filter_by(status=OrderStatus(current_status))
        except ValueError:
            flash('Estado de pedido no valido.', 'warning')
            return redirect(url_for('admin.orders'))

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_number.ilike(like_term),
                Order.customer_name.ilike(like_term),
                Order.customer_email.ilike(like_term),
            )
        )

    parsed_from = _parse_date(date_from)
    if date_from and not parsed_from:
        flash('La fecha inicial no es valida.', 'warning')
        return redirect(url_for('admin.orders'))
    if parsed_from:
        from_start_utc = local_date_to_utc_start(parsed_from)
        query = query.filter(Order.created_at >= from_start_utc)

    parsed_to = _parse_date(date_to)
    if date_to and not parsed_to:
        flash('La fecha final no es valida.', 'warning')
        return redirect(url_for('admin.orders'))
    if parsed_to:
        _, to_end_utc = local_date_range_utc(parsed_to)
        query = query.filter(Order.created_at < to_end_utc)

    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'admin/orders.html',
        orders=pagination.items,
        pagination=pagination,
        current_status=current_status,
        search=search,
        date_from=date_from,
        date_to=date_to,
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
        next_status = OrderStatus(status_value)
    except ValueError:
        flash('Estado de pedido no valido.', 'danger')
        return redirect(url_for('admin.order_detail', id=order.id))

    order.admin_notes = admin_notes
    changed = _append_order_status_history(order, next_status)
    db.session.commit()
    flash(
        'Pedido actualizado correctamente.' if changed else 'Se actualizaron las notas internas del pedido.',
        'success',
    )
    return redirect(url_for('admin.order_detail', id=order.id))

@admin_bp.route('/pedidos/<int:id>/aceptar', methods=['POST'])
@login_required
@admin_required
def order_accept(id):
    from models.order import Order, OrderStatus

    order = Order.query.get_or_404(id)
    changed = _append_order_status_history(order, OrderStatus.CONFIRMADO, 'Pedido aceptado desde el panel admin.')
    if changed:
        db.session.commit()
        flash('Pedido aceptado y marcado como confirmado.', 'success')
    else:
        flash('El pedido ya estaba en ese estado.', 'info')
    return redirect(url_for('admin.order_detail', id=order.id))

@admin_bp.route('/pedidos/<int:id>/rechazar', methods=['POST'])
@login_required
@admin_required
def order_reject(id):
    from models.order import Order, OrderStatus

    order = Order.query.get_or_404(id)
    rejection_reason = request.form.get('rejection_reason', '').strip()

    if not rejection_reason:
        flash('Debes ingresar un motivo de rechazo.', 'danger')
        return redirect(url_for('admin.order_detail', id=order.id))

    _append_order_status_history(order, OrderStatus.RECHAZADO, rejection_reason)
    if order.admin_notes:
        order.admin_notes = f"{order.admin_notes}\n\nMotivo de rechazo: {rejection_reason}"
    else:
        order.admin_notes = f"Motivo de rechazo: {rejection_reason}"
    db.session.commit()
    flash('Pedido rechazado correctamente.', 'success')
    return redirect(url_for('admin.order_detail', id=order.id))

# --- Product CRUD ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg'}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file):
    if not file or file.filename == '':
        return False, 'Debes seleccionar una imagen valida.'

    if not allowed_file(file.filename):
        return False, 'Formato de imagen no permitido.'

    mime_type = (file.mimetype or '').lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, 'El archivo debe ser una imagen JPG o PNG.'

    file.stream.seek(0, os.SEEK_END)
    file_size = file.stream.tell()
    file.stream.seek(0)
    if file_size > MAX_IMAGE_SIZE_BYTES:
        return False, 'La imagen supera el maximo permitido de 5MB.'

    try:
        image = Image.open(file.stream)
        image.verify()
    except Exception:
        file.stream.seek(0)
        return False, 'La imagen subida no es valida o esta corrupta.'

    file.stream.seek(0)
    return True, None

def save_image(file):
    is_valid, error_message = validate_image(file)
    if not is_valid:
        return None, error_message

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))
    return filename, None

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
@limiter.limit("10 per minute")
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
                image_url, error_message = save_image(file)
                if error_message:
                    flash(error_message, 'danger')
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
@limiter.limit("20 per minute")
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
                new_image_url, error_message = save_image(file)
                if new_image_url:
                    # Opcional: eliminar la imagen anterior
                    product.image_url = new_image_url
                else:
                    flash(error_message or 'Formato de imagen no permitido.', 'danger')
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
