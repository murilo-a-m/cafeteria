from flask import Flask, render_template, session

from config import Config
from models import db
from utils import current_user, brl


def create_app():
    # template_folder = views pra ficar com cara de MVC mesmo
    app = Flask(__name__, template_folder="views")
    app.config.from_object(Config)

    db.init_app(app)

    from controllers.shop import shop_bp
    from controllers.cart import cart_bp
    from controllers.account import account_bp
    from controllers.orders import orders_bp
    from controllers.staff import staff_bp
    from controllers.admin import admin_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    app.jinja_env.filters["brl"] = brl

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        count = sum(i["qty"] for i in cart.values())
        return {"user": current_user(), "cart_count": count}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, msg="Você não tem permissão pra acessar essa página."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, msg="Página não encontrada."), 404

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
