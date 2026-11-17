from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db, Product

cart_bp = Blueprint("cart", __name__, url_prefix="/carrinho")

# O carrinho fica na sessao do flask, formato:
# {"3": {"qty": 2, "note": "sem acucar"}, "7": {...}}
# chave e string pq a sessao vira json e json nao aceita chave int


def get_cart():
    return session.get("cart", {})


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


def get_cart_items():
    """monta a lista de itens com produto + subtotal. usado no carrinho e no checkout"""
    cart = get_cart()
    items = []
    subtotal = Decimal("0")
    to_remove = []

    for pid, data in cart.items():
        product = db.session.get(Product, int(pid))
        if product is None or not product.available:
            # produto foi removido/desativado enquanto tava no carrinho
            to_remove.append(pid)
            continue
        line = product.price * data["qty"]
        subtotal += line
        items.append({
            "product": product,
            "qty": data["qty"],
            "note": data.get("note", ""),
            "line_total": line,
        })

    if to_remove:
        for pid in to_remove:
            cart.pop(pid, None)
        save_cart(cart)
        flash("Alguns itens não estão mais disponíveis e foram removidos do carrinho.", "warning")

    return items, subtotal


@cart_bp.route("/")
def view_cart():
    items, subtotal = get_cart_items()
    return render_template("shop/cart.html", items=items, subtotal=subtotal)


@cart_bp.route("/adicionar/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.available:
        flash("Produto indisponível.", "danger")
        return redirect(url_for("shop.index"))

    try:
        qty = int(request.form.get("qty", 1))
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1
    if qty > 20:
        qty = 20  # ninguem pede 50 cafes... se pedir, liga pra loja

    note = request.form.get("note", "").strip()[:200]

    cart = get_cart()
    key = str(product_id)
    if key in cart:
        cart[key]["qty"] = min(cart[key]["qty"] + qty, 20)
        if note:
            cart[key]["note"] = note
    else:
        cart[key] = {"qty": qty, "note": note}
    save_cart(cart)

    flash(f"{product.name} adicionado ao carrinho!", "success")

    # volta pra onde o cliente estava
    back = request.form.get("back")
    if back == "cart":
        return redirect(url_for("cart.view_cart"))
    return redirect(request.referrer or url_for("shop.index"))


@cart_bp.route("/atualizar/<int:product_id>", methods=["POST"])
def update_item(product_id):
    cart = get_cart()
    key = str(product_id)
    if key not in cart:
        return redirect(url_for("cart.view_cart"))

    action = request.form.get("action")
    if action == "plus":
        cart[key]["qty"] = min(cart[key]["qty"] + 1, 20)
    elif action == "minus":
        cart[key]["qty"] -= 1
        if cart[key]["qty"] <= 0:
            cart.pop(key)
    else:
        # veio do campo de observacao
        cart[key]["note"] = request.form.get("note", "").strip()[:200]

    save_cart(cart)
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remover/<int:product_id>", methods=["POST"])
def remove_item(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    save_cart(cart)
    flash("Item removido.", "info")
    return redirect(url_for("cart.view_cart"))
