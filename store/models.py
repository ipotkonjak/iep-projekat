from flask_sqlalchemy import SQLAlchemy;
import json

db = SQLAlchemy();


class ProductCategory(db.Model):
    __tablename__ = "prodcat";

    id = db.Column(db.Integer, primary_key=True);
    productId = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False);
    categoryId = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False);

class Request(db.Model):
    __tablename__ = "request";

    id = db.Column(db.Integer, primary_key=True);
    price = db.Column(db.Float, nullable=False);
    received = db.Column(db.Integer, nullable=False);
    requested = db.Column(db.Integer, nullable=False);
    productId = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False);
    orderId = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False);


class Product(db.Model):
    __tablename__ = "product";

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    categories = db.relationship("Category", secondary=ProductCategory.__table__, back_populates="products");
    orders = db.relationship("Order", secondary=Request.__table__, back_populates="products");



class Category(db.Model):
    __tablename__ = "category";

    id = db.Column(db.Integer, primary_key=True);
    name = db.Column(db.String(256), nullable=False);

    products = db.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories");

    def __repr__(self):
        return self.name;

class Order(db.Model):
    __tablename__ = "order";

    id = db.Column(db.Integer, primary_key=True);
    price = db.Column(db.Float, nullable=False);
    status = db.Column(db.String(256), nullable=False);
    timestamp = db.Column(db.DateTime, nullable=False);
    user = db.Column(db.String(256), nullable=False)


    products = db.relationship("Product", secondary=Request.__table__, back_populates="orders");

    def __repr__(self):
        return self.name;
