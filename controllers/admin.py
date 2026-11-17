import os
import csv
import io
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation

from flask import (Blueprint, render_template, request, redirect, url_for, flash,
                   current_app, Response, abort)

from models import db, Product, CATEGORIES, User, AccessLog, Order, OrderItem
from utils import role_required, current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}


# ----------------------------------------------------------------
# PRODUTOS (US13)
# ----------------------------------------------------------------

@admin_bp.route("/produtos")
@role_required("admin")
def products():
    prods = Product.query.order_by(Product.category, Product.name).all()
    return render_template("admin/products.html", products=prods)


def save_upload(file):
    if not file or file.filename == "":
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return "erro"
    # nome aleatorio pra nao dar conflito
    fname = uuid.uuid4().hex[:12] + "." + ext
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], fname))
    return "uploads/" + fname


@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@role_required("admin")
def product_form(product_id=None):
    p = None
    if product_id:
        p = db.session.get(Product, product_id)
        if not p:
            abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category")
        price_raw = request.form.get("price", "").replace(",", ".")

        try:
            price = Decimal(price_raw)
        except InvalidOperation:
            price = None

        if not name or category not in CATEGORIES or price is None or price <= 0:
            flash("Confira nome, categoria e preço.", "danger")
            return render_template("admin/product_form.html", p=p, form=request.form, categories=CATEGORIES)

        img = save_upload(request.files.get("image"))
        if img == "erro":
            flash("Formato de imagem não aceito (use png, jpg ou webp).", "danger")
            return render_template("admin/product_form.html", p=p, form=request.form, categories=CATEGORIES)

        if p is None:
            p = Product()
            db.session.add(p)
        p.name = name
        p.category = category
        p.price = price
        p.description = request.form.get("description", "").strip()
        p.available = bool(request.form.get("available"))
        if img:
            p.image = img
        db.session.commit()

        flash("Produto salvo!", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", p=p, form={}, categories=CATEGORIES)


@admin_bp.route("/produtos/<int:product_id>/excluir", methods=["POST"])
@role_required("admin")
def delete_product(product_id):
    p = db.session.get(Product, product_id)
    if not p:
        abort(404)
    used = OrderItem.query.filter_by(product_id=p.id).count()
    if used:
        # se ja foi vendido nao da pra apagar (quebra o historico), entao so esconde
        p.available = False
        flash("Esse produto já tem vendas, então foi apenas desativado.", "warning")
    else:
        db.session.delete(p)
        flash("Produto excluído.", "info")
    db.session.commit()
    return redirect(url_for("admin.products"))


# ----------------------------------------------------------------
# USUARIOS (US15)
# ----------------------------------------------------------------

@admin_bp.route("/usuarios")
@role_required("admin")
def users():
    all_users = User.query.order_by(User.role, User.name).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/usuarios/<int:user_id>", methods=["POST"])
@role_required("admin")
def update_user(user_id):
    u = db.session.get(User, user_id)
    if not u:
        abort(404)
    me = current_user()

    if u.id == me.id:
        # nao deixa o admin se rebaixar / se desativar sem querer
        flash("Você não pode alterar o seu próprio perfil por aqui.", "warning")
        return redirect(url_for("admin.users"))

    action = request.form.get("action")
    if action == "toggle":
        u.active = not u.active
        flash(f"Conta de {u.name} {'ativada' if u.active else 'desativada'}.", "info")
    elif action == "role":
        new_role = request.form.get("role")
        if new_role in ("cliente", "atendente", "admin"):
            u.role = new_role
            flash(f"{u.name} agora é {new_role}.", "info")
    db.session.commit()
    return redirect(url_for("admin.users"))


@admin_bp.route("/acessos")
@role_required("admin")
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.created_at.desc()).limit(200).all()
    return render_template("admin/logs.html", logs=logs)


# ----------------------------------------------------------------
# RELATORIO DE VENDAS (US14)
# ----------------------------------------------------------------

def parse_date(txt, fallback):
    try:
        return datetime.strptime(txt, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


def get_report_data(args):
    today = date.today()
    d_from = parse_date(args.get("de"), today - timedelta(days=6))
    d_to = parse_date(args.get("ate"), today)
    if d_from > d_to:
        d_from, d_to = d_to, d_from
    category = args.get("categoria", "")
    product_id = args.get("produto", "")

    start = datetime.combine(d_from, datetime.min.time())
    end = datetime.combine(d_to + timedelta(days=1), datetime.min.time())

    q = (db.session.query(OrderItem, Order, Product)
         .join(Order, OrderItem.order_id == Order.id)
         .join(Product, OrderItem.product_id == Product.id)
         .filter(Order.payment_status == "aprovado")
         .filter(Order.paid_at >= start, Order.paid_at < end))
    if category in CATEGORIES:
        q = q.filter(Product.category == category)
    if product_id.isdigit():
        q = q.filter(Product.id == int(product_id))

    rows = q.all()

    # agrupando na mao mesmo, e pouca coisa
    by_product = {}
    by_day = {}
    order_ids = set()
    total = Decimal("0")

    for item, order, prod in rows:
        line = item.unit_price * item.quantity
        total += line
        order_ids.add(order.id)

        if prod.id not in by_product:
            by_product[prod.id] = {"name": prod.name, "category": prod.category_label(), "qty": 0, "total": Decimal("0")}
        by_product[prod.id]["qty"] += item.quantity
        by_product[prod.id]["total"] += line

        day = order.paid_at.date()
        by_day[day] = by_day.get(day, Decimal("0")) + line

    # preenche os dias sem venda com zero pro grafico nao ficar buracado
    days = []
    d = d_from
    while d <= d_to:
        days.append((d, by_day.get(d, Decimal("0"))))
        d += timedelta(days=1)

    products_sorted = sorted(by_product.values(), key=lambda x: x["total"], reverse=True)

    return {
        "d_from": d_from, "d_to": d_to, "category": category, "product_id": product_id,
        "total": total, "orders_count": len(order_ids), "products": products_sorted, "days": days,
    }


@admin_bp.route("/relatorio")
@role_required("admin")
def report():
    data = get_report_data(request.args)
    max_day = max([v for _, v in data["days"]] + [Decimal("1")])
    all_products = Product.query.order_by(Product.name).all()
    return render_template("admin/report.html", data=data, max_day=max_day,
                           categories=CATEGORIES, all_products=all_products)


@admin_bp.route("/relatorio.csv")
@role_required("admin")
def report_csv():
    data = get_report_data(request.args)
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")  # ; pro excel em pt-br abrir certinho
    w.writerow(["Relatorio de vendas", data["d_from"].strftime("%d/%m/%Y"), data["d_to"].strftime("%d/%m/%Y")])
    w.writerow([])
    w.writerow(["Produto", "Categoria", "Quantidade", "Total (R$)"])
    for p in data["products"]:
        w.writerow([p["name"], p["category"], p["qty"], str(p["total"]).replace(".", ",")])
    w.writerow([])
    w.writerow(["Dia", "Total (R$)"])
    for d, v in data["days"]:
        w.writerow([d.strftime("%d/%m/%Y"), str(v).replace(".", ",")])
    w.writerow([])
    w.writerow(["TOTAL", "", "", str(data["total"]).replace(".", ",")])

    # BOM no inicio pro excel reconhecer acento
    content = "﻿" + out.getvalue()
    fname = f"vendas_{data['d_from']}_{data['d_to']}.csv"
    return Response(content, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={fname}"})
