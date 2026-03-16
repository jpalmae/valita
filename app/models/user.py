from extensions import db, login_manager
from flask_login import UserMixin
from utils.datetime import utc_now

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
