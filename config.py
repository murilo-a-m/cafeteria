import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # trocar isso em producao!!
    SECRET_KEY = os.environ.get("SECRET_KEY", "cafe-gourmet-dev-123")

    # mysql no pythonanywhere: mysql+pymysql://usuario:senha@host/cafeteria
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "cafeteria.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB pra foto ta bom

    # 30 dias logado (US07)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30
