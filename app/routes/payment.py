from flask import Blueprint, request, jsonify, current_app
import hashlib
import hmac
from extensions import csrf, limiter
from utils.mercadopago import get_payment_info, reconcile_order_from_payment_info

payment_bp = Blueprint('payment', __name__)


def _parse_signature_header(signature_header):
    values = {}
    for part in (signature_header or '').split(','):
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        values[key.strip()] = value.strip()
    return values


def _is_valid_webhook_signature():
    secret = current_app.config.get("MP_WEBHOOK_SECRET")
    if not secret:
        current_app.logger.warning("MercadoPago webhook received without MP_WEBHOOK_SECRET configured.")
        return True

    signature_header = request.headers.get("X-Signature", "")
    request_id = request.headers.get("X-Request-Id", "")
    signature_data = _parse_signature_header(signature_header)
    ts = signature_data.get("ts")
    received_hash = signature_data.get("v1")
    data_id = request.args.get("data.id")

    payload = request.get_json(silent=True) or {}
    if not data_id:
        data_id = str((payload.get("data") or {}).get("id") or "")

    if not ts or not received_hash or not request_id or not data_id:
        current_app.logger.warning(
            "MercadoPago webhook signature rejected due to missing fields.",
            extra={"request_id": request_id, "data_id": data_id},
        )
        return False

    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    expected_hash = hmac.new(
        secret.encode("utf-8"),
        msg=manifest.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_hash, received_hash)

@payment_bp.route("/mp/webhook", methods=["POST"])
@csrf.exempt # Webhooks de MercadoPago no envían token CSRF
@limiter.limit("60 per minute")
def mercadopago_webhook():
    if not _is_valid_webhook_signature():
        return jsonify({"status": "invalid signature"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "ignored"}), 200
        
    if data.get("type") == "payment":
        payment_id = data["data"]["id"]
        payment_info = get_payment_info(payment_id)

        if not payment_info:
            return jsonify({"status": "no token configured"}), 200
        reconcile_order_from_payment_info(payment_info)
    
    return jsonify({"status": "ok"}), 200
