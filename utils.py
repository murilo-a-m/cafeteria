from functools import wraps
from flask import session, redirect, url_for, flash, request, abort

from models import db, User


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    user = db.session.get(User, uid)
    # se o admin desativar a conta, derruba a sessao
    if user and not user.active:
        session.pop("user_id", None)
        return None
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("account.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    # uso: @role_required("admin") ou @role_required("atendente", "admin")
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("account.login", next=request.path))
            if user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return deco


def brl(value):
    """format 12.5 -> R$ 12,50"""
    if value is None:
        value = 0
    s = f"{float(value):,.2f}"
    # troca , por . e vice versa (padrao brasileiro)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def only_digits(txt):
    return "".join(c for c in (txt or "") if c.isdigit())
