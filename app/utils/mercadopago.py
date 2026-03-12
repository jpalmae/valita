import mercadopago
from flask import current_app
from models.order import Order

def create_preference(order: Order) -> dict:
    access_token = current_app.config.get("MP_ACCESS_TOKEN")
    if not access_token:
        # Modo fallback para desarrollo si no hay token
        return {"id": "123456-fallback-preference", "init_point": "/pago/exito"}
        
    sdk = mercadopago.SDK(access_token)
    
    items = [{
        "id": str(item.product_id),
        "title": item.product_name,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price),
        "currency_id": "CLP"
    } for item in order.items]
    
    base_url = current_app.config.get("BASE_URL")
    
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
