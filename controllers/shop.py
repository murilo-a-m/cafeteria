from flask import Blueprint, render_template, request, abort

from models import db, Product, CATEGORIES

shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/")
def index():
    products = Product.query.filter_by(available=True).order_by(Product.category, Product.name).all()
    # o filtro e feito no JS (sem recarregar), mas se vier ?cat= na url ja abre filtrado
    selected = request.args.get("cat", "todos")
    return render_template("shop/index.html", products=products, categories=CATEGORIES, selected=selected)


@shop_bp.route("/produto/<int:product_id>")
def product_page(product_id):
    p = db.session.get(Product, product_id)
    if p is None or not p.available:
        abort(404)
    return render_template("shop/product.html", p=p)
