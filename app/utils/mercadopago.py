import mercadopago
from flask import current_app

from extensions import db
from models.order import Order, OrderStatus
from utils.email import send_order_confirmation_email


def get_sdk():
    access_token = current_app.config.get("MP_ACCESS_TOKEN")
    if not access_token:
        return None
    return mercadopago.SDK(access_token)


def get_payment_info(payment_id):
    sdk = get_sdk()
    if not sdk or not payment_id:
        return None
    return sdk.payment().get(str(payment_id))["response"]


def reconcile_order_from_payment_info(payment_info):
    if not payment_info:
        return None

    order_number = payment_info.get("external_reference")
    status = payment_info.get("status")
    payment_id = payment_info.get("id")
    if not order_number:
        return None

    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        current_app.logger.warning(
            "MercadoPago payment received for unknown order.",
            extra={"order_number": order_number, "payment_id": payment_id},
        )
        return None

    previous_payment_status = order.payment_status
    order.mp_payment_id = str(payment_id) if payment_id else order.mp_payment_id
    if status:
        order.payment_status = status
    if status == "approved" and order.status == OrderStatus.RECIBIDO:
        order.status = OrderStatus.RECIBIDO
    db.session.commit()

    if status == "approved" and previous_payment_status != "approved":
        try:
            send_order_confirmation_email(order)
        except Exception:
            current_app.logger.exception(
                "Failed to send order confirmation email.",
                extra={"order_number": order.order_number, "payment_id": payment_id},
            )

    return order


def create_preference(order: Order) -> dict:
    sdk = get_sdk()
    if not sdk:
        # Modo fallback para desarrollo si no hay token
        return {"id": "123456-fallback-preference", "init_point": "/pago/exito"}
    
    items = [{
        "id": str(item.product_id),
        "title": item.product_name,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price),
        "currency_id": "CLP"
    } for item in order.items]
    
    base_url = (current_app.config.get("BASE_URL") or "").rstrip("/")
    
    preference_data = {
        "items": items,
        "payer": {
            "name": order.customer_name,
            "email": order.customer_email,
        },
        "back_urls": {
            "success": f"{base_url}/pago/exito",
            "failure": f"{base_url}/pago/fallo",
            "pending": f"{base_url}/pago/pendiente",
        },
        "auto_return": "approved",
        "notification_url": f"{base_url}/mp/webhook",
        "external_reference": order.order_number,
        "statement_descriptor": "PATITASALG",
    }
    
    result = sdk.preference().create(preference_data)
    return result["response"]
