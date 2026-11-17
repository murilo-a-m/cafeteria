from datetime import datetime, date

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash

from models import db, Order
from utils import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/painel")

ACTIVE = ["recebido", "em_preparo", "saiu"]


@staff_bp.route("/")
@role_required("atendente", "admin")
def panel():
    return render_template("staff/panel.html")


@staff_bp.route("/pedidos.json")
@role_required("atendente", "admin")
def orders_json():
    # pedidos em andamento, do mais antigo pro mais novo (ordem de chegada - US11)
    active = (Order.query.filter(Order.status.in_(ACTIVE))
              .order_by(Order.paid_at.asc()).all())

    start_today = datetime.combine(date.today(), datetime.min.time())
    done_today = (Order.query.filter(Order.status == "entregue", Order.delivered_at >= start_today)
                  .order_by(Order.delivered_at.desc()).limit(10).all())

    def to_dict(o):
        return {
            "id": o.id,
            "status": o.status,
            "label": o.status_label(),
            "next": o.next_status(),
            "time": (o.paid_at or o.created_at).strftime("%H:%M"),
            "customer": o.customer.name,
            "address": o.address_text,
            "total": float(o.total),
            "items": [
                {"name": i.product_name, "qty": i.quantity, "notes": i.notes or ""}
                for i in o.items
            ],
        }

    return jsonify(active=[to_dict(o) for o in active],
                   done=[to_dict(o) for o in done_today])


@staff_bp.route("/pedido/<int:order_id>/avancar", methods=["POST"])
@role_required("atendente", "admin")
def advance_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(ok=False, msg="pedido nao encontrado"), 404

    nxt = order.next_status()
    if nxt is None:
        return jsonify(ok=False, msg="pedido ja finalizado"), 400

    order.status = nxt
    if nxt == "entregue":
        order.delivered_at = datetime.now()
    db.session.commit()

    # TODO avisar o cliente por email/push (US10)

    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(ok=True, status=order.status, label=order.status_label())
    flash(f"Pedido #{order.id}: {order.status_label()}", "success")
    return redirect(url_for("staff.panel"))
