from datetime import timedelta
import os

dbURL = os.environ["DATABASE_URL"]

class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{dbURL}/store"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    REDIS_HOST = "redis"
    REDIS_PRODUCTS_LIST = "products"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"

