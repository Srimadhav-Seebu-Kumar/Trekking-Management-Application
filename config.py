import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Default admin account, created programmatically on first run.
    DEFAULT_ADMIN_NAME = "System Admin"
    DEFAULT_ADMIN_EMAIL = "admin@trekking.com"
    DEFAULT_ADMIN_PASSWORD = "Admin@123"
