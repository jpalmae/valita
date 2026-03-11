from flask import Blueprint, render_template
from models.product import Product

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    # Agrupar por categoría
    categories = {}
    for p in products:
        cat = p.category or 'Otros'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
        
    return render_template('store/index.html', categories=categories)

@main_bp.route('/producto/<int:id>')
def product_detail(id):
    product = Product.query.filter_by(id=id, is_active=True).first_or_404()
    return render_template('store/product_detail.html', product=product)

# Context processor temporal para inyectar cantidad del carrito en todas las plantillas (se implementa real en el paso 5)
@main_bp.context_processor
def inject_cart():
    from flask import session
    cart = session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    return dict(cart_count=cart_count)

@main_bp.route('/pedido/<order_number>')
def order_tracking(order_number):
    from models.order import Order
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('store/tracking.html', order=order)
