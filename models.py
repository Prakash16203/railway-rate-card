# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # we will initialize it from app.py

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # plain text for now
    role = db.Column(db.String(20), nullable=False)            # 'customer' or 'admin'
    email = db.Column(db.String(100))

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Rate(db.Model):
    __tablename__ = 'rates'
    id = db.Column(db.Integer, primary_key=True)
    from_station = db.Column(db.String(50), nullable=False)
    to_station = db.Column(db.String(50), nullable=False)
    train_number = db.Column(db.String(20))
    rate_card = db.Column(db.String(100), nullable=False)
    slr = db.Column(db.String(100))

    def __repr__(self):
        return f"<Rate {self.from_station} → {self.to_station}>"

class AccountGroup(db.Model):
    __tablename__ = 'account_groups'
    sr_no = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), unique=True, nullable=False)
    remark = db.Column(db.Text)

    def __repr__(self):
        return f"<AccountGroup {self.group_name}>"

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), nullable=False)
    account_group = db.Column(db.String(50))               # ← keep this
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    alt_mobile = db.Column(db.String(20))
    address1 = db.Column(db.Text)
    address2 = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pin = db.Column(db.String(10))
    gst = db.Column(db.String(50))
    pan = db.Column(db.String(20))
    aadhaar = db.Column(db.String(20))
    remark = db.Column(db.Text)

    def __repr__(self):
        return f"<Vendor {self.account_name}>"

class RateCard(db.Model):
    __tablename__ = 'rate_cards'
    id = db.Column(db.Integer, primary_key=True)
    train_no = db.Column(db.String(20))
    vehicle_type = db.Column(db.String(50))
    weight_capacity = db.Column(db.String(50))
    parcel_type = db.Column(db.String(50))
    days = db.Column(db.String(100))
    origin_station = db.Column(db.String(50), nullable=False)
    origin_code = db.Column(db.String(20))
    dest_station = db.Column(db.String(50), nullable=False)
    dest_code = db.Column(db.String(20))
    rate_type = db.Column(db.String(50))
    rate_card = db.Column(db.String(100), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    vendor = db.relationship('Vendor', backref='rate_cards')
    origin_person = db.Column(db.String(100))
    origin_mobile = db.Column(db.String(20))
    dest_person = db.Column(db.String(100))
    dest_mobile = db.Column(db.String(20))
    remark = db.Column(db.Text)

    def __repr__(self):
        return f"<RateCard {self.rate_card} - {self.train_no or 'N/A'}>"