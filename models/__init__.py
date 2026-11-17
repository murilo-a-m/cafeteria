from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# import here so db.create_all() knows all the tables
from models.user import User, Address, AccessLog  # noqa
from models.product import Product, CATEGORIES  # noqa
from models.order import Order, OrderItem, Review, ORDER_STATUS  # noqa
