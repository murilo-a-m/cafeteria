from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from models import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    # cliente / atendente / admin
    role = db.Column(db.String(20), nullable=False, default="cliente")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    addresses = db.relationship("Address", backref="user", lazy=True)
    orders = db.relationship("Order", backref="customer", lazy=True)

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    def is_staff(self):
        return self.role in ("atendente", "admin")

    def first_name(self):
        return self.name.split(" ")[0]

    def __repr__(self):
        return f"<User {self.email}>"


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cep = db.Column(db.String(9), nullable=False)
    street = db.Column(db.String(150), nullable=False)
    number = db.Column(db.String(10), nullable=False)
    complement = db.Column(db.String(60))
    district = db.Column(db.String(80))
    city = db.Column(db.String(80))
    state = db.Column(db.String(2))

    def one_line(self):
        txt = f"{self.street}, {self.number}"
        if self.complement:
            txt += f" - {self.complement}"
        txt += f" - {self.district}, {self.city}/{self.state}"
        return txt


class AccessLog(db.Model):
    # log de acessos (US15). bem simples, so registra login/logout
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    email = db.Column(db.String(120))
    action = db.Column(db.String(30))  # login, logout, login_falhou
    ip = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.now)
