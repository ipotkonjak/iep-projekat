from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import db, Product, Category, ProductCategory
from redis import Redis
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_
import io
import csv

app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)


@app.route("/update", methods=["POST"])
@jwt_required(refresh=False)
def update():
    claims = get_jwt()
    roles = claims["roles"]
    if (not "magacioner" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    if not 'file' in request.files:
        return jsonify(message="Field file is missing."), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    ind = 0
    sending = []
    for datRow in reader:
        if (len(datRow) != 4):
            return jsonify(message="Incorrect number of values on line " + str(ind) + "."), 400
        try:
            int(datRow[2])
            if (int(datRow[2]) < 0):
                return jsonify(message="Incorrect quantity on line " + str(ind) + "."), 400
        except ValueError:
            return jsonify(message="Incorrect quantity on line " + str(ind) + "."), 400

        try:
            float(datRow[3])
            if (float(datRow[3]) < 0):
                return jsonify(message="Incorrect price on line " + str(ind) + "."), 400
        except ValueError:
            return jsonify(message="Incorrect price on line " + str(ind) + "."), 400

        ind += 1

        toSend = ",".join(datRow)
        sending.append(toSend)

    for s in sending:
        with Redis(host=Configuration.REDIS_HOST) as redis:
            redis.rpush(Configuration.REDIS_PRODUCTS_LIST, s)

    return Response(status=200)


if (__name__ == "__main__"):
    db.init_app(app)
    app.run(debug=True,host="0.0.0.0", port=5001)
