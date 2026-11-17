from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# importa aqui senao o create_all nao enxerga as tabelas
from models.user import User, Address, AccessLog  # noqa
from models.product import Product, CATEGORIES  # noqa
from models.order import Order, OrderItem, Review, ORDER_STATUS  # noqa
