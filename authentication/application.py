from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import db, User, UserRole;
import re
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity;
from sqlalchemy import and_;

app = Flask(__name__);
app.config.from_object(Configuration);


def checkEmail(email):
    pat = "^[a-zA-Z0-9.-_]+@[a-zA-Z0-9]+\.[a-z]{2,3}$"
    if not re.match(pat, email):
        return False
    else:
        return True


@app.route("/", methods=['GET'])
def index():
    return "radi"


@app.route("/register", methods=["POST"])
def register():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    isCust = request.json.get("isCustomer", None)

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    # isCustEmpty = len(isCust) == 0

    if (forenameEmpty):
        return jsonify(message="Field forename is missing."), 400
    if (surnameEmpty):
        return jsonify(message="Field surname is missing."), 400
    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message="Field password is missing."), 400
    if (isCust is None):
        return jsonify(message="Field isCustomer is missing."), 400

    # pat = "^[a-zA-Z0-9.-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if not checkEmail(email):
        return jsonify(message="Invalid email."), 400
    if (not re.search("[a-z]", password) or not re.search("[A-Z]", password) or not re.search("[0-9]", password) or len(
            password) < 8):
        return jsonify(message="Invalid password."), 400
    user = User.query.filter(User.email == email).first()

    if (user):
        return jsonify(message="Email already exists."), 400

    # return "radi"
    # isCust = isCust == 'True'
    user = User(email=email, password=password, forename=forename, surname=surname, isCustomer=isCust)
    db.session.add(user)
    db.session.commit()

    idRole = 2 if isCust else 3
    userRole = UserRole(userId=user.id, roleId=idRole)
    db.session.add(userRole)
    db.session.commit()

    return Response("Registration successful!", status=200);


jwt = JWTManager(app);


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    # if (emailEmpty or passwordEmpty):
    #     return Response("All fields required!", status=400);

    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400

    if (passwordEmpty):
        return jsonify(message="Field password is missing."), 400
    if not checkEmail(email):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if (not user):
        return jsonify(message="Invalid credentials."), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims);
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims);

    # return Response ( accessToken, status = 200 );
    return jsonify(accessToken=accessToken, refreshToken=refreshToken);


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    };

    return jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)), 200

@app.route("/delete", methods=["POST"])
@jwt_required(refresh=False)
def delete():
    claims = get_jwt()
    roles = claims['roles']
    if(not "admin" in roles):
        return jsonify(msg="Missing Authorization Header"), 401

    email = request.json.get("email", "")

    emailEmpty = len(email) == 0

    if (emailEmpty):
        return jsonify(message="Field email is missing."), 400
    if not checkEmail(email):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(User.email == email).first();

    if (not user):
        return jsonify(message="Unknown user."), 400

    db.session.delete(user)
    db.session.commit()

    return Response("radi", status=200)

if (__name__ == "__main__"):
    db.init_app(app);
    app.run(debug=True,host="0.0.0.0", port=5002);
