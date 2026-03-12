from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from models.product import Product
from models.order import Order, OrderStatus, OrderStatusHistory
from models.order_item import OrderItem
from extensions import db, limiter
from utils.mercadopago import create_preference
from datetime import datetime
import random
import string

checkout_bp = Blueprint('checkout', __name__)

@checkout_bp.route('/carrito')
def cart():
    cart_data = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart_data.values())
    total = subtotal # Envío 0 por ahora
    return render_template('store/cart.html', cart=cart_data, subtotal=subtotal, total=total)

@checkout_bp.route('/carrito/agregar', methods=['POST'])
@limiter.limit("60 per minute")
def add_to_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({"success": False, "message": "Producto no encontrado"}), 404
        
    cart = session.get('cart', {})
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {
            "product_id": product.id,
            "name": product.name,
            "price": float(product.price),
            "quantity": quantity,
            "image_url": product.image_url
        }
        
    session['cart'] = cart
    session.modified = True
    
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    return jsonify({
        "success": True, 
        "cart_count": cart_count,
        "cart_total": cart_total,
        "message": "Producto agregado"
    })

@checkout_bp.route('/carrito/actualizar', methods=['POST'])
@limiter.limit("60 per minute")
def update_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', {})
    
    if product_id in cart:
        if quantity > 0:
            cart[product_id]['quantity'] = quantity
        else:
            del cart[product_id]
            
        session['cart'] = cart
        session.modified = True
        
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
        
    return jsonify({
        "success": True, 
        "cart_count": cart_count,
        "cart_total": cart_total
    })

@checkout_bp.route('/carrito/eliminar', methods=['POST'])
@limiter.limit("60 per minute")
def remove_from_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    
    cart = session.get('cart', {})
    
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
        session.modified = True
        
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
        
    return jsonify({
        "success": True, 
        "cart_count": cart_count,
        "cart_total": cart_total
    })

def generate_order_number():
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"VAL-{date_str}-{random_str}"

@checkout_bp.route('/checkout', methods=['GET', 'POST'])
@limiter.limit("20 per hour", methods=["POST"])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('main.index'))
        
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    total = subtotal
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        rut = request.form.get('rut')
        address = request.form.get('address')
        notes = request.form.get('notes')
        
        order = Order(
            order_number=generate_order_number(),
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=address,
            customer_rut=rut,
            notes=notes,
            subtotal=subtotal,
            shipping_cost=0,
            total=total,
            status=OrderStatus.RECIBIDO,
            payment_status='pending'
        )
        db.session.add(order)
        db.session.flush()

        db.session.add(
            OrderStatusHistory(
                order_id=order.id,
                previous_status=None,
                new_status=OrderStatus.RECIBIDO,
                note='Pedido creado desde checkout.',
                changed_by='cliente',
            )
        )
        
        for item in cart.values():
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                product_name=item['name'],
                unit_price=item['price'],
                quantity=item['quantity'],
                subtotal=item['price'] * item['quantity']
            )
            db.session.add(order_item)
            
        db.session.commit()
        
        pref_response = create_preference(order)
        order.mp_preference_id = pref_response.get('id')
        db.session.commit()
        
        init_point = pref_response.get('init_point', url_for('checkout.success'))
        return redirect(init_point)
        
    return render_template('checkout/form.html', cart=cart, subtotal=subtotal, total=total)

@checkout_bp.route('/pago/exito')
def success():
    session.pop('cart', None)
    return render_template('checkout/success.html')

@checkout_bp.route('/pago/fallo')
def failure():
    return render_template('checkout/failure.html')

@checkout_bp.route('/pago/pendiente')
def pending():
    return render_template('checkout/pending.html')
