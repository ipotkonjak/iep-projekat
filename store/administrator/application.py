import json
import datetime

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import db, Product, Category, ProductCategory, Request, Order
from redis import Redis
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_,or_, func, desc, asc
from sqlalchemy.sql.functions import coalesce
from collections import OrderedDict


app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)


@app.route("/productStatistics", methods=["GET"])
@jwt_required(refresh=False)
def productStatistics():
    claims = get_jwt()
    roles = claims["roles"]
    if (not "admin" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    prodInfo = Product.query.join(Request).with_entities(Product.name, coalesce(func.sum(Request.received), 0), coalesce(func.sum(Request.requested),0)).\
        group_by(Product.id, Product.name).all()

    toSend = []

    for prod in prodInfo:
        elem = {
            "name": prod[0],
            "sold": int(str((prod[2]))),
            "waiting": int(str((prod[2] - prod[1])))
        }
        toSend.append(elem)

    return jsonify(statistics=toSend), 200

@app.route("/categoryStatistics", methods=["GET"])
@jwt_required(refresh=False)
def categoryStatistics():
    claims = get_jwt()
    roles = claims["roles"]
    if (not "admin" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    catInfo = Category.query.outerjoin(ProductCategory).outerjoin(Request, ProductCategory.productId == Request.productId).with_entities(Category.name)\
        .group_by(Category.id, Category.name).order_by(desc(func.sum(Request.requested)), asc(Category.name)).all()
    catInfo = [c[0] for c in catInfo]
    return jsonify(statistics=catInfo), 200



if (__name__ == "__main__"):
    db.init_app(app)
    app.run(debug=True,host="0.0.0.0", port=5003)