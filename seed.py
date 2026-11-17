# dados pra teste. python seed.py --reset apaga tudo e cria de novo
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

from app import app
from models import db, User, Product, Order, OrderItem, Address

PRODUCTS = [
    ("Espresso", "bebidas", "7.50", "Café expresso"),
    ("Cappuccino", "bebidas", "13.90", "Café com leite vaporizado e espuma"),
    ("Latte caramelo", "bebidas", "16.50", "Expresso, leite e calda de caramelo"),
    ("Mocha", "bebidas", "15.90", "Café com chocolate e leite"),
    ("Cold Brew", "bebidas", "14.00", "Café gelado, extraído a frio"),
    ("Chai latte", "bebidas", "14.50", "Chá com especiarias e leite"),
    ("Croissant de chocolate", "doces", "11.90", "Recheado com chocolate"),
    ("Cheesecake", "doces", "18.90", "Fatia"),
    ("Brownie", "doces", "9.90", ""),
    ("Cookie", "doces", "8.50", "Com gotas de chocolate"),
    ("Pão de Queijo (6 un)", "salgados", "12.00", ""),
    ("Croissant de presunto e queijo", "salgados", "14.90", ""),
    ("Kit Café da Manhã", "kits", "59.90", "2 cappuccinos, 2 croissants, pão de queijo e suco"),
    ("Cesta presente", "kits", "129.90", "Café em grãos 250g, caneca e cookies"),
]


def run(reset=False):
    with app.app_context():
        if reset:
            print("apagando tudo...")
            db.drop_all()
        db.create_all()

        if User.query.first():
            print("Banco ja tem dados. Use --reset pra recriar.")
            return

        admin = User(name="Admin", email="admin@cafeteria.com", role="admin")
        admin.set_password("admin123")
        atendente = User(name="Juliana", email="atendente@cafeteria.com", role="atendente")
        atendente.set_password("atend123")
        cliente = User(name="Murilo", email="cliente@teste.com", role="cliente", phone="(41) 98765-4321")
        cliente.set_password("cliente123")
        db.session.add_all([admin, atendente, cliente])

        for name, cat, price, desc in PRODUCTS:
            db.session.add(Product(name=name, category=cat, price=Decimal(price), description=desc))
        db.session.commit()

        addr = Address(user_id=cliente.id, cep="80240-210", street="Rua Bento Viana", number="1120",
                       district="Batel", city="Curitiba", state="PR")
        db.session.add(addr)
        db.session.commit()

        # uns pedidos antigos pro relatorio nao ficar vazio
        prods = Product.query.all()
        for days_ago in range(1, 8):
            for _ in range(random.randint(1, 4)):
                when = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 8))
                chosen = random.sample(prods, random.randint(1, 3))
                o = Order(user_id=cliente.id, status="entregue", address_text=addr.one_line(), cep=addr.cep,
                          payment_method=random.choice(["pix", "credito"]), payment_status="aprovado",
                          subtotal=0, delivery_fee=Decimal("6.90"), total=0, eta_minutes=35,
                          created_at=when, paid_at=when, delivered_at=when + timedelta(minutes=40))
                if o.payment_method == "credito":
                    o.card_last4 = "1111"
                sub = Decimal("0")
                for p in chosen:
                    q = random.randint(1, 2)
                    o.items.append(OrderItem(product_id=p.id, product_name=p.name, unit_price=p.price, quantity=q))
                    sub += p.price * q
                o.subtotal = sub
                o.total = sub + o.delivery_fee
                db.session.add(o)
        db.session.commit()

        print("ok")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
