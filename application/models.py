from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    
    reservations = db.relationship('Reservation', backref='user')


class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.Integer,nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    total_spots_left= db.Column(db.Integer, nullable=False)
    
    spots = db.relationship('ParkingSpot', backref='parking_lot', cascade="all, delete-orphan") 
    reservation=db.relationship('Reservation',backref='parking_lot')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.total_spots_left is None:
            self.total_spots_left = self.total_spots

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    
    reservations = db.relationship('Reservation', backref='parking_spot')

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'))
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False) 
    vehicle_number = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime,default=None)
    end_time = db.Column(db.DateTime,default=None)
    price_per_hour = db.Column(db.Float)
    payment_status = db.Column(db.String, default="bookedin", nullable=False)

class ParkingHistory(db.Model):  
    __tablename__ = 'parking_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime,default=None)
    end_time = db.Column(db.DateTime,default=None)
    price_per_hour = db.Column(db.Float, nullable=False)
    lot_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.Integer, nullable=False)