from datetime import datetime, timedelta
from models import db

# ordem importa! o painel usa isso pra saber qual o proximo status
ORDER_STATUS = ["recebido", "em_preparo", "saiu", "entregue"]

STATUS_LABELS = {
    "aguardando_pagamento": "Aguardando pagamento",
    "recebido": "Recebido",
    "em_preparo": "Em preparo",
    "saiu": "Saiu para entrega",
    "entregue": "Entregue",
    "cancelado": "Cancelado",
}


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="aguardando_pagamento")

    # endereco copiado no momento do pedido. se o cliente apagar o endereco depois
    # o pedido antigo continua com o endereco certo
    address_text = db.Column(db.String(300), nullable=False)
    cep = db.Column(db.String(9))

    payment_method = db.Column(db.String(10))  # pix / credito / debito
    payment_status = db.Column(db.String(20), default="pendente")  # pendente, aprovado, recusado
    card_last4 = db.Column(db.String(4))
    pix_code = db.Column(db.String(200))

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    eta_minutes = db.Column(db.Integer, default=40)

    created_at = db.Column(db.DateTime, default=datetime.now)
    paid_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    review = db.relationship("Review", backref="order", uselist=False)

    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    def next_status(self):
        if self.status not in ORDER_STATUS:
            return None
        i = ORDER_STATUS.index(self.status)
        if i + 1 < len(ORDER_STATUS):
            return ORDER_STATUS[i + 1]
        return None

    def estimated_arrival(self):
        base = self.paid_at or self.created_at
        return base + timedelta(minutes=self.eta_minutes or 40)

    def can_be_reviewed(self):
        # avaliacao so ate 48h depois de entregue
        if self.status != "entregue" or self.review is not None:
            return False
        if not self.delivered_at:
            return False
        return datetime.now() - self.delivered_at <= timedelta(hours=48)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(100))  # snapshot do nome
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(200))

    product = db.relationship("Product")

    def line_total(self):
        return self.unit_price * self.quantity


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True)
    stars = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
