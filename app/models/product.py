from extensions import db
from utils.datetime import utc_now

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=-1)
    image_url = db.Column(db.String(300), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(80), nullable=True)
    weight_grams = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
