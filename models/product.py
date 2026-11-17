from datetime import datetime
from models import db

# categorias fixas por enquanto, nao vale a pena fazer tabela so pra isso
CATEGORIES = {
    "bebidas": "Bebidas",
    "doces": "Doces",
    "salgados": "Salgados",
    "kits": "Kits e Cestas",
}


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(200))  # path relativo dentro de /static
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def category_label(self):
        return CATEGORIES.get(self.category, self.category)

    def image_url(self):
        if self.image:
            return "/static/" + self.image
        # no photo -> generic picture of the category
        return f"/static/img/products/{self.category}.svg"
