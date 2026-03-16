from decimal import Decimal

import resend
from flask import current_app, render_template


def _base_url():
    return (current_app.config.get("BASE_URL") or "").rstrip("/")


def _format_currency(amount):
    numeric_amount = Decimal(amount or 0)
    return f"${numeric_amount:,.0f}".replace(",", ".")


def resend_is_configured():
    return bool(
        current_app.config.get("RESEND_API_KEY")
        and current_app.config.get("RESEND_FROM_EMAIL")
    )


def send_order_confirmation_email(order):
    if not resend_is_configured():
        current_app.logger.warning(
            "Skipping order confirmation email because Resend is not configured.",
            extra={"order_number": order.order_number},
        )
        return False

    resend.api_key = current_app.config["RESEND_API_KEY"]

    tracking_url = f"{_base_url()}/pedido/{order.order_number}"
    subject = f"Confirmamos tu pedido {order.order_number}"
    html = render_template(
        "emails/order_confirmation.html",
        order=order,
        tracking_url=tracking_url,
        format_currency=_format_currency,
    )
    text = "\n".join(
        [
            f"Hola {order.customer_name},",
            "",
            "Tu pago fue aprobado y recibimos tu pedido.",
            f"Pedido: {order.order_number}",
            f"Total: {_format_currency(order.total)}",
            f"Seguimiento: {tracking_url}",
            "",
            "Gracias por comprar en Chocolates Patitas de Algodón.",
        ]
    )

    payload = {
        "from": f"{current_app.config['RESEND_FROM_NAME']} <{current_app.config['RESEND_FROM_EMAIL']}>",
        "to": [order.customer_email],
        "subject": subject,
        "html": html,
        "text": text,
    }

    reply_to = current_app.config.get("RESEND_REPLY_TO")
    if reply_to:
        payload["reply_to"] = reply_to

    response = resend.Emails.send(payload)
    current_app.logger.info(
        "Order confirmation email sent with Resend.",
        extra={
            "order_number": order.order_number,
            "customer_email": order.customer_email,
            "resend_id": response.get("id"),
        },
    )
    return True
