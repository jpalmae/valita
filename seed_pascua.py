import sys
from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    p1 = Product(
        name="Cono de Huevitos de Pascua",
        description="Delicioso cono surtido de huevitos de chocolate en papel metálico morado y azul, acompañado de tiernas figuras artesanales de pascua.",
        price=6990,
        stock=50,
        category="Especial Pascua",
        image_url="cono_huevitos_pascua.png",
        is_active=True
    )
    p2 = Product(
        name="Caja Premium de Pascua",
        description="Elegante caja kraft con una selección premium de huevitos artesanales surtidos y detalles de zanahoria en chocolate.",
        price=14990,
        stock=30,
        category="Especial Pascua",
        image_url="caja_huevitos_pascua.png",
        is_active=True
    )
    p3 = Product(
        name="Plato de Huevitos Decorados",
        description="Exclusiva selección de huevitos de chocolate oscuro y blanco pintados a mano con detalles primaverales, servidos listos para compartir.",
        price=12500,
        stock=20,
        category="Especial Pascua",
        image_url="huevitos_decorados_plato.png",
        is_active=True
    )
    p4 = Product(
        name="Bolsa de Huevitos Artesanales",
        description="Bolsita de regalo que incluye huevitos decorados con chispas de colores, rayas y estrellas, junto a figuras encantadoras de la temporada.",
        price=8500,
        stock=40,
        category="Especial Pascua",
        image_url="huevitos_decorados_bolsa.png",
        is_active=True
    )

    db.session.add(p1)
    db.session.add(p2)
    db.session.add(p3)
    db.session.add(p4)
    db.session.commit()
    print("Productos de Pascua agregados exitosamente!")

