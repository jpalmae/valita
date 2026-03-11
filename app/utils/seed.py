from extensions import db
from models.product import Product
from models.user import User
from config import Config
import bcrypt

def seed_admin():
    if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
        hashed = bcrypt.hashpw(Config.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(
            email=Config.ADMIN_EMAIL,
            password=hashed,
            name='Administrador',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created: {Config.ADMIN_EMAIL}")

def seed_products():
    products = [
        {"name": "Tableta Bitter 70%", "price": 4990, "category": "Tabletas",
         "description": "Chocolate amargo con 70% cacao ecuatoriano", "weight_grams": 80},
        {"name": "Bombones Surtidos x12", "price": 12990, "category": "Bombones",
         "description": "Caja con 12 bombones artesanales variados", "weight_grams": 180},
        {"name": "Gift Box Premium", "price": 24990, "category": "Gift Box",
         "description": "Caja regalo con selección premium de chocolates", "weight_grams": 350},
        {"name": "Trufas de Champagne x6", "price": 8990, "category": "Trufas",
         "description": "Trufas artesanales con champagne Moët", "weight_grams": 90},
        {"name": "Tableta Leche & Avellanas", "price": 3990, "category": "Tabletas",
         "description": "Chocolate de leche con avellanas tostadas", "weight_grams": 80},
        {"name": "Cono de Huevitos de Pascua", "price": 6990, "category": "Regalos Especiales",
         "description": "Delicioso cono surtido de huevitos de chocolate en papel metalico morado y azul, acompanado de tiernas figuras artesanales de pascua.",
         "image_url": "cono_huevitos_pascua.png"},
        {"name": "Caja Premium de Pascua", "price": 14990, "category": "Regalos Especiales",
         "description": "Elegante caja kraft con una seleccion premium de huevitos artesanales surtidos y detalles de zanahoria en chocolate.",
         "image_url": "caja_huevitos_pascua.png"},
        {"name": "Plato de Huevitos Decorados", "price": 12500, "category": "Regalos Especiales",
         "description": "Exclusiva seleccion de huevitos de chocolate oscuro y blanco pintados a mano con detalles primaverales, servidos listos para compartir.",
         "image_url": "huevitos_decorados_plato.png"},
        {"name": "Bolsa de Huevitos Artesanales", "price": 8500, "category": "Regalos Especiales",
         "description": "Bolsita de regalo que incluye huevitos decorados con chispas de colores, rayas y estrellas, junto a figuras encantadoras de la temporada.",
         "image_url": "huevitos_decorados_bolsa.png"},
    ]

    created = 0
    for p_data in products:
        if Product.query.filter_by(name=p_data["name"]).first():
            continue

        product = Product(**p_data, is_active=True, stock=-1)
        db.session.add(product)

        created += 1

    db.session.commit()
    if created == 0:
        print("Products already seeded.")
    else:
        print(f"{created} products seeded.")
