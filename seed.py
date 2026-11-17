"""
Popula o banco com dados iniciais pra testar.
Rodar UMA vez:  python seed.py
(se quiser zerar tudo: python seed.py --reset)
"""
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

from app import app
from models import db, User, Product, Order, OrderItem, Address

PRODUCTS = [
    # nome, categoria, preco, descricao
    ("Espresso", "bebidas", "7.50", "Dose curta de café especial, grãos do Cerrado Mineiro."),
    ("Cappuccino Italiano", "bebidas", "13.90", "Espresso, leite vaporizado e bastante espuma."),
    ("Latte de Caramelo", "bebidas", "16.50", "Espresso com leite e calda de caramelo da casa."),
    ("Mocha", "bebidas", "15.90", "Café, chocolate belga e leite cremoso."),
    ("Cold Brew", "bebidas", "14.00", "Extração a frio por 18h. Suave e refrescante."),
    ("Chá Chai Latte", "bebidas", "14.50", "Blend de especiarias com leite vaporizado."),
    ("Croissant de Chocolate", "doces", "11.90", "Massa folhada amanteigada recheada com chocolate."),
    ("Cheesecake de Frutas Vermelhas", "doces", "18.90", "Fatia generosa com calda artesanal."),
    ("Brownie com Nozes", "doces", "9.90", "Brownie úmido de chocolate 70%."),
    ("Cookie Gigante", "doces", "8.50", "Gotas de chocolate ao leite, crocante por fora."),
    ("Pão de Queijo (6 un)", "salgados", "12.00", "Feito com queijo canastra."),
    ("Croissant Presunto e Queijo", "salgados", "14.90", "Quentinho, saído do forno."),
    ("Kit Café da Manhã", "kits", "59.90", "2 cappuccinos, 2 croissants, pão de queijo e suco."),
    ("Cesta Presente Gourmet", "kits", "129.90", "Café em grãos 250g, caneca, cookies e chocolates."),
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

        admin = User(name="Administrador", email="admin@cafeteria.com", role="admin")
        admin.set_password("admin123")
        atendente = User(name="Ana Atendente", email="atendente@cafeteria.com", role="atendente")
        atendente.set_password("atend123")
        cliente = User(name="Cliente Teste", email="cliente@teste.com", role="cliente", phone="(41) 99999-0000")
        cliente.set_password("cliente123")
        db.session.add_all([admin, atendente, cliente])

        for name, cat, price, desc in PRODUCTS:
            db.session.add(Product(name=name, category=cat, price=Decimal(price), description=desc))
        db.session.commit()

        addr = Address(user_id=cliente.id, cep="80010-000", street="Rua XV de Novembro", number="700",
                       district="Centro", city="Curitiba", state="PR")
        db.session.add(addr)
        db.session.commit()

        # alguns pedidos antigos pro relatorio e historico nao ficarem vazios
        prods = Product.query.all()
        random.seed(42)
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

        print("Pronto! Usuarios criados:")
        print("  admin@cafeteria.com / admin123")
        print("  atendente@cafeteria.com / atend123")
        print("  cliente@teste.com / cliente123")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
