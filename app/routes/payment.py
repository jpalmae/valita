from flask import Blueprint, request, jsonify, current_app
import mercadopago
from extensions import db
from models.order import Order, OrderStatus
from extensions import csrf

payment_bp = Blueprint('payment', __name__)

@payment_bp.route("/mp/webhook", methods=["POST"])
@csrf.exempt # Webhooks de MercadoPago no envían token CSRF
def mercadopago_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "ignored"}), 200
        
    if data.get("type") == "payment":
        payment_id = data["data"]["id"]
        access_token = current_app.config.get("MP_ACCESS_TOKEN")
        
        if not access_token:
            return jsonify({"status": "no token configured"}), 200
            
        sdk = mercadopago.SDK(access_token)
        payment_info = sdk.payment().get(payment_id)["response"]
        
        order_number = payment_info.get("external_reference")
        status = payment_info.get("status")  # approved, rejected, pending
        
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            order.mp_payment_id = str(payment_id)
            order.payment_status = status
            if status == "approved" and order.status == OrderStatus.RECIBIDO:
                order.status = OrderStatus.RECIBIDO  # Admin confirma manualmente después
            db.session.commit()
    
    return jsonify({"status": "ok"}), 200
