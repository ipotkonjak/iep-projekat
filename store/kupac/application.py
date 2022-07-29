import json
import datetime

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import db, Product, Category, ProductCategory, Request, Order
from redis import Redis
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_,or_, func
from collections import OrderedDict


app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)


@app.route("/search", methods=["GET"])
@jwt_required(refresh=False)
def update():
    claims = get_jwt()
    roles = claims["roles"]
    if (not "kupac" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    name = request.args.get("name", "")
    category = request.args.get("category", "")

    kategorije = Category.query.join(ProductCategory).join(Product).with_entities(Category.name).filter(
        and_(
            Product.name.like("%{}%".format(name)),
            Category.name.like("%{}%".format(category))
            )
        ).group_by(Category.name).all()
    kategorije = [kat[0] for kat in kategorije]
    proizvodi = Product.query.join(ProductCategory).join(Category).with_entities(Product.id,Product.name,Product.amount,Product.price).filter(
        and_(
            Product.name.like("%{}%".format(name)),
            Category.name.like("%{}%".format(category))
        )
        ).group_by(Product.id).all()

    toSend = []
    for p in proizvodi:
        # return str(p[0])
        kat = ProductCategory.query.join(Category).with_entities(Category.name).filter(
            ProductCategory.productId == p[0]
        ).all()
        kat = [k[0] for k in kat]
        elem = {
            "categories": kat,
            "id": p[0],
            "name": p[1],
            "price": p[3],
            "quantity": p[2]
        }
        toSend.append(elem)

    return jsonify(categories=kategorije, products=toSend)

@app.route("/order", methods=["POST"])
@jwt_required(refresh=False)
def order():
    claims = get_jwt()
    roles = claims["roles"]
    email = claims["sub"]
    if (not "kupac" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    requests = request.json.get("requests", "")

    if(len(requests) <= 0):
        return jsonify(message="Field requests is missing."), 400

    i = 0
    cost = 0
    products = []
    for r in requests:
        if(not "id" in r):
            return jsonify(message="Product id is missing for request number "+ str(i) +"."), 400

        if (not "quantity" in r):
            return jsonify(message="Product quantity is missing for request number " + str(i) + "."), 400

        id = r["id"]
        quantity = r["quantity"]

        try:
            id = int(id)
            if(id <= 0):
                return jsonify(message="Invalid product id for request number " + str(i) + "."), 400
        except ValueError:
            return jsonify(message="Invalid product id for request number " + str(i) + "."), 400

        try:
            quantity = int(quantity)
            if (quantity <= 0):
                return jsonify(message="Invalid product quantity for request number " + str(i) + "."), 400
        except ValueError:
            return jsonify(message="Invalid product quantity for request number " + str(i) + "."), 400

        prod = Product.query.filter(Product.id == id).first()
        products.append(prod)
        if(not prod):
            return jsonify(message="Invalid product for request number " + str(i) + "."), 400
        cost += quantity*prod.price
        i += 1

    order = Order(price=cost, status="PENDING", timestamp=datetime.datetime.now(), user=email)
    db.session.add(order)
    db.session.commit()

    flag = True
    for i in range(len(requests)):
        inStorage = products[i].amount
        quantity = requests[i]["quantity"]
        if(inStorage > quantity):
            inStorage = quantity
        if(inStorage < quantity):
            flag = False
        products[i].amount -= inStorage
        req = Request(requested=quantity, productId=products[i].id, orderId=order.id, price=products[i].price, received=inStorage)
        db.session.add(req)

    if(flag):
        order.status = "COMPLETE"
    db.session.commit()
    return jsonify(id=order.id), 200

@app.route("/status", methods=["GET"])
@jwt_required(refresh=False)
def status():
    claims = get_jwt()
    roles = claims["roles"]
    email = claims["sub"]
    if (not "kupac" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    toSend = []
    ordIds = Order.query.filter(Order.user == email).with_entities(Order.id, Order.price, Order.status, Order.timestamp).all()
    for o in ordIds:
        orders = Order.query.join(Request).join(Product).\
            with_entities(Product.id, Product.name, Request.price, Request.received, Request.requested).filter(
            Order.id == o[0]
        ).all()
        prods = []
        for ords in orders:
            cats = Category.query.join(ProductCategory).with_entities(Category.name).filter(
                ProductCategory.productId == ords[0]
            ).group_by(Category.name).all()
            cats = [c[0] for c in cats]

            elem = {
                "categories": cats,
                "name": ords[1],
                "price": ords[2],
                "received": ords[3],
                "requested": ords[4]
            }
            prods.append(elem)

        elem = OrderedDict({
            "products": prods,
            "price": o[1],
            "status": o[2],
            "timestamp": o[3]
        })
        toSend.append(elem)

    return jsonify(orders=toSend), 200

if (__name__ == "__main__"):
    db.init_app(app)
    app.run(debug=True,host="0.0.0.0", port=5000)
