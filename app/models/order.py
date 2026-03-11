from extensions import db
import enum
from datetime import datetime, timezone

class OrderStatus(enum.Enum):
    RECIBIDO = "recibido"
    CONFIRMADO = "confirmado"
    EN_FABRICACION = "en_fabricacion"
    LISTO_ENTREGA = "listo_para_entrega"
    ENTREGADO = "entregado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    customer_rut = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.RECIBIDO)
    payment_status = db.Column(db.String(50), default='pending') # pending, approved, rejected, cancelled
    mp_payment_id = db.Column(db.String(100), nullable=True)
    mp_preference_id = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    admin_notes = db.Column(db.Text, nullable=True)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
