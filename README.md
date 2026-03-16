# Valita

Tienda online de chocolates artesanales construida con Flask, PostgreSQL, Nginx y Docker Compose.

Branding actual: `Chocolates Patitas de Algodón`.

## Stack

- `Flask`
- `PostgreSQL`
- `SQLAlchemy`
- `Flask-Migrate`
- `Gunicorn`
- `Nginx`
- `Docker Compose`

## Estructura

- `app/`: aplicacion Flask, rutas, modelos, templates y assets
- `db/`: inicializacion de base de datos
- `nginx/`: configuracion del proxy
- `docker-compose.yml`: stack local y de despliegue

## Variables de entorno

Usa `.env.example` como base:

```env
DB_USER=valita_user
DB_PASSWORD=supersecret
SECRET_KEY=flask-secret-muy-larga-cambiar-en-prod
MP_ACCESS_TOKEN=
MP_PUBLIC_KEY=
MP_WEBHOOK_SECRET=
BASE_URL=http://localhost
RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_FROM_NAME=Chocolates Patitas de Algodón
RESEND_REPLY_TO=admin@chocolatesvalita.cl
ADMIN_EMAIL=admin@chocolatesvalita.cl
ADMIN_PASSWORD=Admin1234!
```

## Levantar el proyecto

1. Crear archivo `.env` a partir de `.env.example`.
2. Levantar el stack:

```bash
docker compose up -d --build
```

3. Poblar datos iniciales:

```bash
docker compose exec app flask seed
```

4. Abrir la tienda en:

```text
http://localhost:8888
```

## Panel admin

Acceso por defecto:

- Email: `admin@chocolatesvalita.cl`
- Password: `Admin1234!`

Ruta:

```text
http://localhost:8888/admin/login
```

## Funcionalidades

- Catalogo de productos
- Detalle de producto
- Carrito
- Checkout
- Correo transaccional de confirmación vía Resend cuando el pago queda aprobado
- Seguimiento de pedidos
- Panel admin para:
  - crear productos
  - editar productos
  - activar o desactivar productos
  - eliminar productos sin historial de pedidos
  - gestionar pedidos

## Seed de productos

El comando `flask seed`:

- crea el usuario admin si no existe
- carga productos base
- carga productos de Pascua
- es idempotente por nombre de producto

## Despliegue

El proyecto corre correctamente con:

```bash
docker compose up -d --build
```

Servicios:

- `db`: PostgreSQL
- `app`: Flask + Gunicorn
- `nginx`: proxy publico en puerto `8888`

## Notas

- `.env` no se versiona.
- Los assets publicos de productos viven en `app/static/uploads/`.
- Las fuentes del sitio viven en `app/static/fonts/`.
