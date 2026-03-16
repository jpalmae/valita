from flask import Flask, url_for
from config import Config
from extensions import db, login_manager, migrate, csrf, limiter
import os
from utils.datetime import format_local_datetime, to_local

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter._storage_uri = app.config.get('RATELIMIT_STORAGE_URI', 'memory://')
    limiter.init_app(app)

    # Import models
    import models

    with app.app_context():
        db.create_all()

    # Blueprints
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.checkout import checkout_bp
    from routes.payment import payment_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(payment_bp)

    # Register CLI commands
    from utils.seed import seed_products, seed_admin
    @app.cli.command("seed")
    def seed():
        """Seed database with test data."""
        seed_admin()
        seed_products()
        print("Database seeded successfully!")

    @app.context_processor
    def asset_helpers():
        def asset_url(filename):
            asset_path = os.path.join(app.static_folder, filename)
            version = None
            if os.path.exists(asset_path):
                version = int(os.path.getmtime(asset_path))
            return url_for('static', filename=filename, v=version)

        return {
            'asset_url': asset_url,
            'format_datetime': format_local_datetime,
            'to_local_datetime': to_local,
        }

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
