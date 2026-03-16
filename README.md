# Valita

Tienda online de chocolates artesanales construida con Flask, PostgreSQL, Nginx y Docker Compose.

Branding actual: `Chocolates Patitas de Algodón`.

## Stack

- `Flask`
- `PostgreSQL`
- `SQLAlchemy`
- `Flask-Migrate`
- `Gunicorn`
- `Redis`
- `Nginx`
- `Docker Compose`
- `Tailwind CSS`

## Estructura

- `app/`: aplicación Flask, rutas, modelos, templates y assets
- `db/`: inicialización de base de datos
- `nginx/`: configuración del proxy
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
RATELIMIT_STORAGE_URI=redis://redis:6379/0
BASE_URL=http://localhost
APP_TIMEZONE=America/Santiago
RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_FROM_NAME=Chocolates Patitas de Algodón
RESEND_REPLY_TO=admin@chocolatesvalita.cl
ADMIN_EMAIL=admin@chocolatesvalita.cl
ADMIN_PASSWORD=Admin1234!
```

Variables relevantes:

- `MP_ACCESS_TOKEN`: token productivo de Mercado Pago
- `MP_PUBLIC_KEY`: public key de Mercado Pago
- `MP_WEBHOOK_SECRET`: secreto para validar la firma del webhook
- `BASE_URL`: URL pública del sitio, por ejemplo `https://carol.gplace.io`
- `APP_TIMEZONE`: zona horaria de la app, por defecto `America/Santiago`
- `RESEND_API_KEY`: API key de Resend
- `RESEND_FROM_EMAIL`: remitente verificado en Resend
- `RESEND_REPLY_TO`: correo de respuesta para los correos transaccionales

## Desarrollo local

1. Crear `.env` a partir de `.env.example`.
2. Instalar dependencias frontend:

```bash
npm install
```

3. Compilar CSS:

```bash
npm run build:css
```

4. Levantar el stack:

```bash
docker compose up -d --build
```

5. Poblar datos iniciales:

```bash
docker compose exec app flask seed
```

6. Abrir la tienda:

```text
http://localhost:8888
```

Para desarrollo de estilos:

```bash
npm run watch:css
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

- Catálogo de productos
- Detalle de producto
- Carrito en sesión
- Checkout con Mercado Pago `Checkout Pro`
- Seguimiento público de pedidos
- Correo transaccional de confirmación vía Resend cuando el pago queda aprobado
- Panel admin para:
  - crear productos
  - editar productos
  - activar o desactivar productos
  - eliminar productos sin historial de pedidos
  - gestionar pedidos
  - aceptar o rechazar pedidos
  - revisar historial de cambios

## Seed de productos

El comando `flask seed`:

- crea el usuario admin si no existe
- carga productos base
- carga productos de Pascua
- es idempotente por nombre de producto

## Mercado Pago

La integración usa `Checkout Pro`.

Flujo actual:

1. El checkout crea una preferencia con `back_urls`, `notification_url` y `external_reference`.
2. El cliente paga en Mercado Pago.
3. La app intenta reconciliar el pago por dos vías:
   - webhook en `/mp/webhook`
   - retorno del usuario a `/pago/exito`, `/pago/pendiente` o `/pago/fallo`
4. Cuando el pago queda `approved`, se actualiza:
   - `payment_status`
   - `mp_payment_id`
   - correo de confirmación al cliente

Configuración necesaria:

- `MP_ACCESS_TOKEN`
- `MP_PUBLIC_KEY`
- `MP_WEBHOOK_SECRET`
- `BASE_URL`

URLs relevantes:

- `https://tu-dominio/mp/webhook`
- `https://tu-dominio/pago/exito`
- `https://tu-dominio/pago/fallo`
- `https://tu-dominio/pago/pendiente`

Notas:

- La app valida firma del webhook cuando `MP_WEBHOOK_SECRET` está configurado.
- Si el webhook falla o llega tarde, la reconciliación también puede ocurrir desde las `back_urls`.

## Resend

La app envía correo de confirmación solo cuando el pago queda `approved`.

Configuración necesaria:

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_REPLY_TO`

Recomendaciones:

- `RESEND_FROM_EMAIL` debe pertenecer a un dominio verificado en Resend.
- `RESEND_REPLY_TO` puede ser un correo personal o comercial.

Template actual:

- `app/templates/emails/order_confirmation.html`

Lógica de envío:

- `app/utils/email.py`

## Zona horaria

La app guarda timestamps en UTC y los muestra en la zona definida por `APP_TIMEZONE`.

Valor recomendado para este proyecto:

```env
APP_TIMEZONE=America/Santiago
```

Esto afecta:

- fechas mostradas en admin
- tracking público
- numeración de pedidos por fecha
- filtros y métricas del dashboard

## Despliegue

El proyecto corre con:

```bash
docker compose up -d --build
```

Servicios:

- `db`: PostgreSQL
- `redis`: backend de rate limiting
- `app`: Flask + Gunicorn
- `nginx`: proxy público en puerto `8888`

Notas de operación:

- `nginx` usa resolución dinámica por `127.0.0.11` para no quedarse pegado a IPs viejas del contenedor `app`.
- los uploads viven en el volumen `uploads_data`
- `Flask-Limiter` usa Redis, no memoria local

## Servidor actual

Deploy validado en `jp-personal`:

- Host: `100.80.186.8`
- Usuario SSH: `sixmanager`

Stack del proyecto:

- `valita-db-1`
- `valita-redis-1`
- `valita-app-1`
- `valita-nginx-1`

No deben tocarse otros contenedores ajenos al proyecto.

## Notas

- `.env` no se versiona.
- Los assets públicos de productos viven en `app/static/uploads/`.
- Las fuentes del sitio viven en `app/static/fonts/`.
- Si expones credenciales en conversaciones o logs, rótalas después.
