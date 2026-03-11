# SPEC: Chocolates Valita — Plataforma de Pedidos Online

## Resumen del Proyecto

Aplicación web de e-commerce para la tienda **Chocolates Valita**, que permite a clientes explorar el catálogo, hacer pedidos y pagar en línea vía MercadoPago. Incluye panel de administración para gestionar pedidos y estados de producción/entrega.

Stack tecnológico: **Flask + SQLAlchemy + PostgreSQL + Tailwind CSS**, desplegado en **Docker Compose**.

---

## Arquitectura General

```
chocolates-valita/
├── docker-compose.yml
├── .env.example
├── nginx/
│   └── nginx.conf
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   ├── config.py
│   ├── extensions.py           # db, login_manager, etc.
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py             # Tienda pública
│   │   ├── checkout.py         # Carrito y pago
│   │   ├── payment.py          # Webhooks MercadoPago
│   │   └── admin.py            # Panel de administración
│   ├── templates/
│   │   ├── base.html
│   │   ├── store/
│   │   │   ├── index.html
│   │   │   ├── product_detail.html
│   │   │   └── cart.html
│   │   ├── checkout/
│   │   │   ├── form.html
│   │   │   ├── success.html
│   │   │   └── failure.html
│   │   └── admin/
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── orders.html
│   │       ├── order_detail.html
│   │       ├── products.html
│   │       └── product_form.html
│   ├── static/
│   │   ├── css/
│   │   │   └── output.css      # Tailwind compilado
│   │   ├── js/
│   │   │   ├── cart.js
│   │   │   └── admin.js
│   │   └── uploads/            # Imágenes de productos (volumen Docker)
│   └── utils/
│       ├── mercadopago.py
│       └── decorators.py
└── db/
    └── init.sql
```

---

## Docker Compose

### Servicios

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: chocolates_valita
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 5s
      retries: 10

  app:
    build: ./app
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/chocolates_valita
      SECRET_KEY: ${SECRET_KEY}
      MP_ACCESS_TOKEN: ${MP_ACCESS_TOKEN}
      MP_PUBLIC_KEY: ${MP_PUBLIC_KEY}
      BASE_URL: ${BASE_URL}
      ADMIN_EMAIL: ${ADMIN_EMAIL}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
    volumes:
      - uploads_data:/app/static/uploads
    expose:
      - "5000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - uploads_data:/app/static/uploads:ro
    depends_on:
      - app

volumes:
  postgres_data:
  uploads_data:
```

### Variables de Entorno (.env)

```env
DB_USER=valita_user
DB_PASSWORD=supersecret
SECRET_KEY=flask-secret-muy-larga
MP_ACCESS_TOKEN=APP_USR-xxxx          # Token MercadoPago
MP_PUBLIC_KEY=APP_USR-xxxx
BASE_URL=https://chocolates.tudominio.cl
ADMIN_EMAIL=admin@chocolatesvalita.cl
ADMIN_PASSWORD=Admin1234!
```

---

## Modelos de Base de Datos

### `User` (administradores)

| Campo       | Tipo         | Descripción                     |
|-------------|-------------|----------------------------------|
| id          | Integer PK   |                                  |
| email       | String 150   | Único                            |
| password    | String 256   | Hash bcrypt                      |
| name        | String 100   |                                  |
| is_admin    | Boolean      | Default True (solo admins usan auth) |
| created_at  | DateTime     |                                  |

### `Product`

| Campo        | Tipo         | Descripción                        |
|--------------|-------------|-------------------------------------|
| id           | Integer PK   |                                     |
| name         | String 150   | Nombre del producto                 |
| description  | Text         | Descripción larga                   |
| price        | Numeric(10,2)| Precio en CLP                       |
| stock        | Integer      | Unidades disponibles (-1 = ilimitado)|
| image_url    | String 300   | Ruta relativa a /static/uploads/    |
| is_active    | Boolean      | Visible en tienda                   |
| category     | String 80    | Ej: "Tabletas", "Bombones", "Gift Box"|
| weight_grams | Integer      | Peso en gramos (informativo)        |
| created_at   | DateTime     |                                     |
| updated_at   | DateTime     | Auto-update                        |

### `Order`

| Campo           | Tipo          | Descripción                              |
|-----------------|--------------|-------------------------------------------|
| id              | Integer PK    |                                           |
| order_number    | String 20     | Único, generado: `VAL-YYYYMMDD-XXXX`     |
| customer_name   | String 150    |                                           |
| customer_email  | String 150    |                                           |
| customer_phone  | String 30     |                                           |
| customer_address| Text          | Dirección de entrega                      |
| customer_rut    | String 20     | Opcional, RUT chileno                     |
| notes           | Text          | Notas del cliente                         |
| subtotal        | Numeric(10,2) |                                           |
| shipping_cost   | Numeric(10,2) | Default 0                                 |
| total           | Numeric(10,2) |                                           |
| status          | Enum          | Ver estados abajo                         |
| payment_status  | Enum          | `pending`, `approved`, `rejected`, `cancelled` |
| mp_payment_id   | String 100    | ID de pago MercadoPago                    |
| mp_preference_id| String 150    | ID de preferencia MP                      |
| created_at      | DateTime      |                                           |
| updated_at      | DateTime      |                                           |
| admin_notes     | Text          | Notas internas del admin                  |

#### Estados del Pedido (Enum `OrderStatus`)

```python
class OrderStatus(enum.Enum):
    RECIBIDO          = "recibido"
    CONFIRMADO        = "confirmado"
    EN_FABRICACION    = "en_fabricacion"
    LISTO_ENTREGA     = "listo_para_entrega"
    ENTREGADO         = "entregado"
    RECHAZADO         = "rechazado"
    CANCELADO         = "cancelado"
```

### `OrderItem`

| Campo       | Tipo          | Descripción                        |
|-------------|--------------|-------------------------------------|
| id          | Integer PK    |                                     |
| order_id    | FK → Order    |                                     |
| product_id  | FK → Product  |                                     |
| product_name| String 150    | Snapshot del nombre al momento      |
| unit_price  | Numeric(10,2) | Snapshot del precio al momento      |
| quantity    | Integer       |                                     |
| subtotal    | Numeric(10,2) | unit_price × quantity               |

---

## Rutas y Vistas

### Tienda Pública (`/`)

| Método | Ruta                    | Descripción                              |
|--------|------------------------|------------------------------------------|
| GET    | `/`                     | Landing page con catálogo de productos   |
| GET    | `/producto/<id>`        | Detalle del producto                     |
| GET    | `/carrito`              | Vista del carrito (datos en sessionStorage/API)|
| POST   | `/carrito/agregar`      | API JSON: agregar producto al carrito    |
| POST   | `/carrito/actualizar`   | API JSON: cambiar cantidad               |
| POST   | `/carrito/eliminar`     | API JSON: eliminar ítem                  |
| GET    | `/checkout`             | Formulario datos del cliente             |
| POST   | `/checkout`             | Crear Order + redirigir a MercadoPago    |
| GET    | `/pago/exito`           | Página de éxito post-pago                |
| GET    | `/pago/fallo`           | Página de fallo/rechazo                  |
| GET    | `/pago/pendiente`       | Pago pendiente                           |
| GET    | `/pedido/<order_number>`| Estado del pedido (tracking público)     |

### Webhooks MercadoPago

| Método | Ruta                    | Descripción                              |
|--------|------------------------|------------------------------------------|
| POST   | `/mp/webhook`           | Recibe notificaciones IPN de MP          |

### Panel de Administración (`/admin`)

| Método | Ruta                      | Descripción                              |
|--------|--------------------------|------------------------------------------|
| GET    | `/admin/login`            | Formulario de login                      |
| POST   | `/admin/login`            | Autenticación                            |
| GET    | `/admin/logout`           | Cerrar sesión                            |
| GET    | `/admin/`                 | Dashboard: métricas y pedidos recientes  |
| GET    | `/admin/pedidos`          | Lista de pedidos con filtros             |
| GET    | `/admin/pedidos/<id>`     | Detalle del pedido                       |
| POST   | `/admin/pedidos/<id>/estado` | Cambiar estado del pedido             |
| POST   | `/admin/pedidos/<id>/aceptar` | Aceptar pedido (→ CONFIRMADO)        |
| POST   | `/admin/pedidos/<id>/rechazar`| Rechazar pedido                       |
| GET    | `/admin/productos`        | CRUD productos                           |
| GET    | `/admin/productos/nuevo`  | Formulario nuevo producto                |
| POST   | `/admin/productos/nuevo`  | Crear producto                           |
| GET    | `/admin/productos/<id>/editar` | Formulario editar producto          |
| POST   | `/admin/productos/<id>/editar` | Actualizar producto                 |
| POST   | `/admin/productos/<id>/toggle` | Activar/desactivar producto         |

---

## Integración MercadoPago

### Flujo de Pago

```
Cliente llena checkout form
        ↓
POST /checkout → Crear Order (status=RECIBIDO, payment_status=pending)
        ↓
SDK MP → Crear Preference con items, back_urls, notification_url
        ↓
Redirect → URL de pago de MercadoPago
        ↓
Cliente paga → MP notifica webhook POST /mp/webhook
        ↓
Webhook verifica → Actualiza payment_status en Order
        ↓
Cliente regresa → /pago/exito | /pago/fallo
```

### Utilidad `utils/mercadopago.py`

```python
import mercadopago

def create_preference(order: Order) -> dict:
    sdk = mercadopago.SDK(current_app.config["MP_ACCESS_TOKEN"])
    
    items = [{
        "id": str(item.product_id),
        "title": item.product_name,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price),
        "currency_id": "CLP"
    } for item in order.items]
    
    preference_data = {
        "items": items,
        "payer": {
            "name": order.customer_name,
            "email": order.customer_email,
        },
        "back_urls": {
            "success": f"{BASE_URL}/pago/exito",
            "failure": f"{BASE_URL}/pago/fallo",
            "pending": f"{BASE_URL}/pago/pendiente",
        },
        "auto_return": "approved",
        "notification_url": f"{BASE_URL}/mp/webhook",
        "external_reference": order.order_number,
        "statement_descriptor": "Chocolates Valita",
    }
    
    result = sdk.preference().create(preference_data)
    return result["response"]
```

### Webhook Handler

```python
@payment_bp.route("/mp/webhook", methods=["POST"])
def mercadopago_webhook():
    data = request.json
    if data.get("type") == "payment":
        payment_id = data["data"]["id"]
        sdk = mercadopago.SDK(current_app.config["MP_ACCESS_TOKEN"])
        payment_info = sdk.payment().get(payment_id)["response"]
        
        order_number = payment_info.get("external_reference")
        status = payment_info.get("status")  # approved, rejected, pending
        
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            order.mp_payment_id = str(payment_id)
            order.payment_status = status
            if status == "approved" and order.status == OrderStatus.RECIBIDO:
                order.status = OrderStatus.RECIBIDO  # Admin confirma manualmente
            db.session.commit()
    
    return jsonify({"status": "ok"}), 200
```

---

## Diseño UI/UX

### Paleta de Colores (Tailwind custom)

```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      chocolate: {
        50:  '#fdf6f0',
        100: '#fae8d4',
        200: '#f4cda5',
        300: '#eca96c',
        400: '#e07d35',
        500: '#c85d1a',
        600: '#9e3f0e',
        700: '#7a2e0a',
        800: '#5e2008',
        900: '#3d1305',
      },
      cream: '#FFF8F0',
      gold: '#C9A84C',
    },
    fontFamily: {
      serif: ['Playfair Display', 'Georgia', 'serif'],
      sans: ['Lato', 'system-ui', 'sans-serif'],
    }
  }
}
```

### Páginas Principales

#### Landing / Tienda (`/`)
- Hero section con imagen de banner (chocolates artesanales)
- Sección de categorías con íconos
- Grid de productos: tarjetas con foto, nombre, precio, botón "Agregar al carrito"
- Carrito flotante (sidebar o drawer) con badge de cantidad en header
- Footer con datos de contacto, redes sociales e información de pago seguro

#### Detalle de Producto
- Imagen grande
- Descripción completa
- Precio destacado
- Selector de cantidad
- Botón "Agregar al carrito"
- Sección de características (peso, ingredientes, alérgenos)

#### Carrito
- Lista de ítems con foto pequeña, nombre, cantidad (editable), precio unitario, subtotal
- Botón eliminar por ítem
- Resumen: subtotal, envío, **total**
- CTA "Proceder al Checkout"

#### Checkout
- Formulario datos cliente:
  - Nombre completo (requerido)
  - Email (requerido)
  - Teléfono (requerido)
  - RUT (opcional)
  - Dirección de entrega (requerido)
  - Notas adicionales (opcional)
- Resumen del pedido al costado
- Botón "Pagar con MercadoPago"

#### Tracking Público (`/pedido/<order_number>`)
- Timeline visual con los estados
- Datos básicos del pedido (número, fecha, total)
- Estado de pago

### Panel de Administración

#### Dashboard
- Cards de métricas:
  - Pedidos hoy / esta semana / este mes
  - Ingresos del mes
  - Pedidos pendientes de confirmación
  - Pedidos en fabricación
- Tabla de últimos 10 pedidos
- Gráfico simple de pedidos por día (últimos 30 días) — Chart.js

#### Lista de Pedidos (`/admin/pedidos`)
- Filtros: estado, rango de fechas, búsqueda por nombre/email/número
- Tabla con columnas: N° pedido, cliente, fecha, total, estado pago, estado pedido, acciones
- Paginación (20 por página)
- Badge de color por estado:
  - `RECIBIDO` → amarillo
  - `CONFIRMADO` → azul
  - `EN_FABRICACION` → naranja
  - `LISTO_ENTREGA` → verde claro
  - `ENTREGADO` → verde
  - `RECHAZADO` → rojo

#### Detalle del Pedido
- Info completa del cliente
- Tabla de ítems pedidos
- Total y estado de pago
- Acciones:
  - **Aceptar pedido** (→ CONFIRMADO) — botón verde, con confirmación
  - **Rechazar pedido** — botón rojo, pide motivo (textarea)
  - **Cambiar estado** — dropdown con todos los estados válidos
  - Campo **Notas internas** (solo visible en admin)
- Historial de cambios de estado (timestamps automáticos)

#### CRUD Productos
- Lista con foto miniatura, nombre, precio, stock, estado
- Toggle activo/inactivo
- Formulario:
  - Nombre, categoría (select), descripción (textarea)
  - Precio (número, CLP)
  - Stock (número, -1 = ilimitado)
  - Peso en gramos
  - Subir imagen (JPG/PNG, max 5MB)
  - Vista previa de imagen

---

## Carrito de Compras

El carrito se almacena en **Flask session** (server-side), serializado como dict:

```python
# session["cart"] = {
#   "product_id_str": {
#     "product_id": int,
#     "name": str,
#     "price": float,
#     "quantity": int,
#     "image_url": str
#   }
# }
```

API endpoints retornan JSON con:
```json
{
  "success": true,
  "cart_count": 3,
  "cart_total": 15900,
  "message": "Producto agregado"
}
```

---

## Seguridad

- Autenticación admin con **Flask-Login** + sesiones firmadas
- Passwords hasheadas con **bcrypt**
- CSRF protection con **Flask-WTF** en todos los formularios
- Validación de webhook MP: verificar `X-Signature` header
- Rate limiting en endpoints de pago con **Flask-Limiter**
- Headers de seguridad via nginx: `X-Frame-Options`, `X-XSS-Protection`, `CSP`
- Upload de imágenes: validar extensión + tipo MIME, nombre aleatorio con `uuid4`
- Variables de entorno: nunca hardcodear secrets

---

## Dependencias Python

```txt
# requirements.txt
flask==3.1.0
flask-sqlalchemy==3.1.1
flask-login==0.6.3
flask-wtf==1.2.1
flask-limiter==3.7.0
psycopg2-binary==2.9.9
mercadopago==2.3.0
bcrypt==4.1.2
pillow==10.3.0
python-dotenv==1.0.1
gunicorn==21.2.0
alembic==1.13.1
flask-migrate==4.0.5
wtforms==3.1.2
email-validator==2.1.1
```

---

## Dockerfile de la App

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static/uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "run:app"]
```

---

## Nginx Config

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location /static/uploads/ {
        alias /app/static/uploads/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /static/ {
        alias /app/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Inicialización y Datos de Prueba

```python
# app/utils/seed.py — Ejecutar solo en desarrollo
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
    ]
    for p_data in products:
        product = Product(**p_data, is_active=True, stock=-1)
        db.session.add(product)
    db.session.commit()
```

---

## Comandos de Desarrollo

```bash
# Levantar todo
docker compose up -d

# Ver logs
docker compose logs -f app

# Aplicar migraciones
docker compose exec app flask db upgrade

# Sembrar datos de prueba
docker compose exec app flask seed

# Shell de Flask
docker compose exec app flask shell

# Rebuild app
docker compose up -d --build app
```

---

## Notas para el Agente de IA

1. **Tailwind**: Usar CDN en desarrollo, compilar con CLI de Node para producción. El `output.css` va en `/app/static/css/`.

2. **Imágenes de productos**: En desarrollo usar imágenes placeholder (Unsplash/Lorem Picsum). El admin puede subir imágenes reales vía formulario.

3. **MercadoPago Chile**: Usar credenciales de sandbox para desarrollo. El Access Token de producción va en `.env`. Las notificaciones webhook requieren URL pública (usar ngrok en desarrollo).

4. **Orden de implementación sugerida**:
   1. Modelos + DB + migraciones
   2. Autenticación admin
   3. CRUD de productos (admin)
   4. Tienda pública (catálogo + detalle)
   5. Carrito (session-based)
   6. Checkout + integración MercadoPago
   7. Webhook + actualización de estados
   8. Panel de pedidos (admin)
   9. Tracking público
   10. Dashboard con métricas
   11. Polish UI/UX

5. **MercadoPago SDK**: `pip install mercadopago`. Documentación: https://www.mercadopago.cl/developers/es/docs

6. **Formateo de precios**: Siempre mostrar en formato chileno: `$ 12.990` (punto como separador de miles, sin decimales para CLP).

7. **Responsive**: La tienda debe ser mobile-first. El panel admin puede ser desktop-primary pero funcional en tablet.

8. **Notificaciones**: Solo panel de administración por ahora. Sin integraciones externas de mensajería en v1.
