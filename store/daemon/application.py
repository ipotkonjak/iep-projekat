from flask import Flask
from configuration import Configuration
from models import db, Product, ProductCategory, Category, Order, Request
from redis import Redis
from flask_jwt_extended import JWTManager
from sqlalchemy import asc, func

app = Flask(__name__)
app.config.from_object(Configuration)
jwt = JWTManager(app)

def main():
    while True:
        try:
            with Redis(host=Configuration.REDIS_HOST) as redis:
                while True:
                    podaci = redis.blpop(Configuration.REDIS_PRODUCTS_LIST)[1].decode().split(",")
                    kategorije = podaci[0].split("|")
                    ime = podaci[1]
                    kolicina = int(podaci[2])
                    cena = float(podaci[3])

                    # print(str(podaci))
                    with app.app_context():
                        proizvod = Product.query.filter(Product.name == ime).first()
                        if(proizvod):
                            postojece = ProductCategory.query.join(Category).with_entities(Category.name).filter(ProductCategory.productId == proizvod.id).all()
                            postojece = [p[0] for p in postojece]
                            if(set(kategorije) == set(postojece)):
                                proizvod.price = (proizvod.price*proizvod.amount + cena*kolicina)/(proizvod.amount + kolicina)
                                proizvod.amount += kolicina

                                db.session.commit()
                                ordIds = Order.query.join(Request).with_entities(Order.id, Request.id).filter(
                                    Order.status == "PENDING",
                                    Request.productId == proizvod.id,
                                    Request.received < Request.requested
                                ).group_by(Order.id, Request.id).order_by(asc(Order.id)).all()
                                for o in ordIds:
                                    order = Order.query.filter(Order.id == o[0]).first()
                                    req = Request.query.filter(Request.id == o[1]).first()
                                    num = Request.query.with_entities(func.count("*")).filter(
                                        Request.orderId == order.id,
                                        Request.received < Request.requested
                                    ).all()

                                    cnt = req.requested - req.received
                                    if (cnt <= proizvod.amount):
                                        proizvod.amount -= cnt
                                        req.received += cnt
                                        if (num[0][0] == 1):
                                            order.status = "COMPLETE"
                                    else:
                                        req.received += proizvod.amount
                                        proizvod.amount = 0
                                    db.session.commit()
                                    if (proizvod.amount == 0):
                                        break
                            else:
                                continue
                        else:
                            noviProizvod = Product(name=ime, price=cena, amount=kolicina)
                            db.session.add(noviProizvod)
                            db.session.commit()

                            for kat in kategorije:
                                novaKategorija = Category.query.filter(Category.name == kat).first()
                                if(not novaKategorija):
                                    novaKategorija = Category(name=kat)
                                    db.session.add(novaKategorija)
                                    db.session.commit()

                                noviLink = ProductCategory(productId=noviProizvod.id, categoryId=novaKategorija.id)
                                db.session.add(noviLink)
                                db.session.commit()
        except Exception as error:
            print(error, flush=True)

if(__name__ == "__main__"):
    db.init_app(app)
    main()