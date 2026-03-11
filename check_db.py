from app import create_app
from app.models.product import Product
app = create_app()
app.app_context().push()
products = Product.query.all()
for p in products:
    print(f"{p.id}: {p.name} - img: {p.image_url} - active: {p.is_active} - cat: {p.category}")
