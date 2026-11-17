from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort

from models import db, Order, OrderItem, Address, Review, Product
from models.order import ORDER_STATUS
from utils import current_user, login_required, brl
from services.delivery import calc_delivery
from services import payment_gateway
from controllers.cart import get_cart_items, get_cart, save_cart
from controllers.account import build_address_from_form

orders_bp = Blueprint("orders", __name__, url_prefix="/pedido")


@orders_bp.route("/frete")
def delivery_quote():
    # chamado via fetch no checkout quando o cliente digita o CEP
    cep = request.args.get("cep", "")
    result = calc_delivery(cep)
    if result is None:
        return jsonify(ok=False, msg="Ainda não entregamos nesse CEP :(")
    fee, minutes = result
    return jsonify(ok=True, fee=fee, fee_txt=brl(fee), minutes=minutes)


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user = current_user()
    items, subtotal = get_cart_items()
    if not items:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("shop.index"))

    if request.method == "GET":
        return render_template("orders/checkout.html", items=items, subtotal=subtotal,
                               addresses=user.addresses, form={})

    form = request.form

    addr_choice = form.get("address_id", "new")
    if addr_choice != "new":
        addr = db.session.get(Address, int(addr_choice))
        if not addr or addr.user_id != user.id:
            abort(400)
    else:
        addr = build_address_from_form(form)
        if addr is None:
            flash("Preencha o endereço de entrega (CEP, rua e número).", "danger")
            return render_template("orders/checkout.html", items=items, subtotal=subtotal,
                                   addresses=user.addresses, form=form)
        if form.get("save_address"):
            addr.user_id = user.id
            db.session.add(addr)
            # commit vai junto com o pedido la embaixo

    quote = calc_delivery(addr.cep)
    if quote is None:
        flash("Infelizmente ainda não entregamos nesse CEP.", "danger")
        db.session.rollback()
        return render_template("orders/checkout.html", items=items, subtotal=subtotal,
                               addresses=user.addresses, form=form)

    fee, minutes = quote
    fee = Decimal(str(fee))
    total = subtotal + fee

    method = form.get("payment_method")
    if method not in ("pix", "credito", "debito"):
        flash("Escolha a forma de pagamento.", "danger")
        return render_template("orders/checkout.html", items=items, subtotal=subtotal,
                               addresses=user.addresses, form=form)

    # cartao: cobra ANTES de criar o pedido. se recusar nem cria
    card_result = None
    if method in ("credito", "debito"):
        card_result = payment_gateway.charge_card(
            form.get("card_number", ""),
            form.get("card_holder", ""),
            form.get("card_expiry", ""),
            form.get("card_cvv", ""),
            float(total),
        )
        if not card_result.approved:
            db.session.rollback()
            flash(card_result.message, "danger")
            return render_template("orders/checkout.html", items=items, subtotal=subtotal,
                                   addresses=user.addresses, form=form, payment_error=True)

    order = Order(
        user_id=user.id,
        address_text=addr.one_line(),
        cep=addr.cep,
        payment_method=method,
        subtotal=subtotal,
        delivery_fee=fee,
        total=total,
        eta_minutes=minutes,
    )
    for it in items:
        order.items.append(OrderItem(
            product_id=it["product"].id,
            product_name=it["product"].name,
            unit_price=it["product"].price,
            quantity=it["qty"],
            notes=it["note"],
        ))

    if card_result:
        order.payment_status = "aprovado"
        order.card_last4 = card_result.last4
        order.status = "recebido"
        order.paid_at = datetime.now()

    db.session.add(order)
    db.session.commit()

    if method == "pix":
        order.pix_code = payment_gateway.generate_pix_code(order.id, float(total))
        db.session.commit()
        return redirect(url_for("orders.pix_payment", order_id=order.id))

    save_cart({})
    flash("Pagamento aprovado! Seu pedido foi enviado pra cafeteria ☕", "success")
    return redirect(url_for("orders.order_detail", order_id=order.id))


def get_order_or_404(order_id):
    order = db.session.get(Order, order_id)
    user = current_user()
    if order is None:
        abort(404)
    # cliente so ve o proprio pedido, funcionario ve todos
    if order.user_id != user.id and not user.is_staff():
        abort(403)
    return order


@orders_bp.route("/<int:order_id>/pix")
@login_required
def pix_payment(order_id):
    order = get_order_or_404(order_id)
    if order.payment_status == "aprovado":
        return redirect(url_for("orders.order_detail", order_id=order.id))
    return render_template("orders/pix.html", order=order)


@orders_bp.route("/<int:order_id>/pix/confirmar", methods=["POST"])
@login_required
def confirm_pix(order_id):
    # SIMULACAO: na vida real quem confirma e o webhook do banco
    order = get_order_or_404(order_id)
    if order.payment_status != "aprovado":
        order.payment_status = "aprovado"
        order.status = "recebido"
        order.paid_at = datetime.now()
        db.session.commit()
        save_cart({})
        flash("Pix recebido! Seu pedido foi enviado pra cafeteria ☕", "success")
    return redirect(url_for("orders.order_detail", order_id=order.id))


@orders_bp.route("/<int:order_id>")
@login_required
def order_detail(order_id):
    order = get_order_or_404(order_id)
    if order.status == "aguardando_pagamento":
        return redirect(url_for("orders.pix_payment", order_id=order.id))
    return render_template("orders/detail.html", order=order, steps=ORDER_STATUS)


@orders_bp.route("/<int:order_id>/status")
@login_required
def order_status_json(order_id):
    order = get_order_or_404(order_id)
    return jsonify(
        status=order.status,
        label=order.status_label(),
        eta=order.estimated_arrival().strftime("%H:%M"),
        can_review=order.can_be_reviewed(),
    )


@orders_bp.route("/<int:order_id>/avaliar", methods=["POST"])
@login_required
def review_order(order_id):
    order = get_order_or_404(order_id)
    if order.user_id != current_user().id:
        abort(403)
    if not order.can_be_reviewed():
        flash("Esse pedido não pode mais ser avaliado.", "warning")
        return redirect(url_for("orders.order_detail", order_id=order.id))

    try:
        stars = int(request.form.get("stars", 0))
    except ValueError:
        stars = 0
    if stars < 1 or stars > 5:
        flash("Escolha de 1 a 5 estrelas.", "danger")
        return redirect(url_for("orders.order_detail", order_id=order.id))

    r = Review(order_id=order.id, stars=stars, comment=request.form.get("comment", "").strip()[:500])
    db.session.add(r)
    db.session.commit()
    flash("Obrigado pela avaliação!", "success")
    return redirect(url_for("orders.order_detail", order_id=order.id))


@orders_bp.route("/<int:order_id>/repetir", methods=["POST"])
@login_required
def reorder(order_id):
    order = get_order_or_404(order_id)
    cart = get_cart()
    skipped = 0
    for item in order.items:
        p = db.session.get(Product, item.product_id)
        if not p or not p.available:
            skipped += 1
            continue
        key = str(p.id)
        if key in cart:
            cart[key]["qty"] = min(cart[key]["qty"] + item.quantity, 20)
        else:
            cart[key] = {"qty": item.quantity, "note": item.notes or ""}
    save_cart(cart)

    if skipped:
        flash(f"{skipped} item(ns) não estão mais disponíveis e ficaram de fora.", "warning")
    else:
        flash("Itens adicionados ao carrinho!", "success")
    return redirect(url_for("cart.view_cart"))
