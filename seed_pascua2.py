import os
import sys

# Ensure the app directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    # Only add if they don't exist
    if not Product.query.filter_by(name='Cono de Huevitos de Pascua').first():
        p1 = Product(
            name='Cono de Huevitos de Pascua',
            description='Delicioso cono surtido de huevitos de chocolate en papel metálico morado y azul, acompañado de tiernas figuras artesanales de pascua.',
            price=6990,
            stock=50,
            category='Regalos Especiales',
            image_url='cono_huevitos_pascua.png',
            is_active=True
        )
        db.session.add(p1)
    
    if not Product.query.filter_by(name='Caja Premium de Pascua').first():
        p2 = Product(
            name='Caja Premium de Pascua',
            description='Elegante caja kraft con una selección premium de huevitos artesanales surtidos y detalles de zanahoria en chocolate.',
            price=14990,
            stock=30,
            category='Regalos Especiales',
            image_url='caja_huevitos_pascua.png',
            is_active=True
        )
        db.session.add(p2)
        
    if not Product.query.filter_by(name='Plato de Huevitos Decorados').first():
        p3 = Product(
            name='Plato de Huevitos Decorados',
            description='Exclusiva selección de huevitos de chocolate oscuro y blanco pintados a mano con detalles primaverales, servidos listos para compartir.',
            price=12500,
            stock=20,
            category='Regalos Especiales',
            image_url='huevitos_decorados_plato.png',
            is_active=True
        )
        db.session.add(p3)
        
    if not Product.query.filter_by(name='Bolsa de Huevitos Artesanales').first():
        p4 = Product(
            name='Bolsa de Huevitos Artesanales',
            description='Bolsita de regalo que incluye huevitos decorados con chispas de colores, rayas y estrellas, junto a figuras encantadoras de la temporada.',
            price=8500,
            stock=40,
            category='Regalos Especiales',
            image_url='huevitos_decorados_bolsa.png',
            is_active=True
        )
        db.session.add(p4)

    db.session.commit()
    print('Productos de Pascua agregados exitosamente!')

