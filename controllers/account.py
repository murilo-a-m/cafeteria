from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db, User, Address, AccessLog, Order
from utils import current_user, login_required, only_digits

account_bp = Blueprint("account", __name__, url_prefix="/conta")


def log_access(user, email, action):
    entry = AccessLog(
        user_id=user.id if user else None,
        email=email,
        action=action,
        ip=request.headers.get("X-Forwarded-For", request.remote_addr),
    )
    db.session.add(entry)
    db.session.commit()


def safe_next(default):
    nxt = request.args.get("next") or request.form.get("next")
    # evita redirect pra outro site (open redirect)
    if nxt and nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return default


@account_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("shop.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        pwd2 = request.form.get("password2", "")
        phone = request.form.get("phone", "").strip()

        errors = []
        if len(name) < 3:
            errors.append("Informe seu nome completo.")
        if "@" not in email or "." not in email:
            errors.append("E-mail inválido.")
        if len(pwd) < 6:
            errors.append("A senha precisa ter pelo menos 6 caracteres.")
        if pwd != pwd2:
            errors.append("As senhas não conferem.")
        if User.query.filter_by(email=email).first():
            errors.append("Já existe uma conta com esse e-mail.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("account/register.html", form=request.form)

        user = User(name=name, email=email, phone=phone, role="cliente")
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()

        session.permanent = True
        session["user_id"] = user.id
        log_access(user, email, "cadastro")
        flash(f"Bem-vindo(a), {user.first_name()}!", "success")
        return redirect(safe_next(url_for("shop.index")))

    return render_template("account/register.html", form={})


@account_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(pwd):
            log_access(user, email, "login_falhou")
            flash("E-mail ou senha incorretos.", "danger")
            return render_template("account/login.html", email=email)

        if not user.active:
            flash("Sua conta está desativada. Fale com a loja.", "danger")
            return render_template("account/login.html", email=email)

        # "lembrar de mim" sempre ligado, a pedido da US07
        session.permanent = True
        session["user_id"] = user.id
        log_access(user, email, "login")

        # funcionario cai direto no painel
        if user.is_staff():
            default = url_for("staff.panel")
        else:
            default = url_for("shop.index")
        return redirect(safe_next(default))

    return render_template("account/login.html", email="")


@account_bp.route("/logout")
def logout():
    user = current_user()
    if user:
        log_access(user, user.email, "logout")
    session.pop("user_id", None)
    # o carrinho eu deixo, vai que a pessoa so trocou de conta
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("shop.index"))


@account_bp.route("/")
@login_required
def my_account():
    user = current_user()
    orders = (Order.query.filter_by(user_id=user.id)
              .filter(Order.status != "aguardando_pagamento")
              .order_by(Order.created_at.desc()).all())
    return render_template("account/my_account.html", orders=orders, addresses=user.addresses)


@account_bp.route("/enderecos/novo", methods=["POST"])
@login_required
def add_address():
    user = current_user()
    addr = build_address_from_form(request.form)
    if addr is None:
        flash("Preencha CEP, rua e número.", "danger")
    else:
        addr.user_id = user.id
        db.session.add(addr)
        db.session.commit()
        flash("Endereço salvo.", "success")
    return redirect(request.referrer or url_for("account.my_account"))


@account_bp.route("/enderecos/<int:addr_id>/excluir", methods=["POST"])
@login_required
def delete_address(addr_id):
    addr = db.session.get(Address, addr_id)
    if addr and addr.user_id == current_user().id:
        db.session.delete(addr)
        db.session.commit()
        flash("Endereço removido.", "info")
    return redirect(url_for("account.my_account"))


def build_address_from_form(form):
    # tambem uso isso no checkout
    cep = only_digits(form.get("cep"))
    street = form.get("street", "").strip()
    number = form.get("number", "").strip()
    if len(cep) != 8 or not street or not number:
        return None
    return Address(
        cep=cep[:5] + "-" + cep[5:],
        street=street,
        number=number,
        complement=form.get("complement", "").strip(),
        district=form.get("district", "").strip(),
        city=form.get("city", "").strip(),
        state=form.get("state", "").strip().upper()[:2],
    )
