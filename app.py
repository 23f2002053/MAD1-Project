from flask import Flask
from flask import render_template
from application.models import db,User,ParkingLot,ParkingSpot,Reservation,ParkingHistory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

app = None
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///lmsdata.sqlite3"
    app.config['SECRET_KEY'] = 'a-very-long-but-random-secret-key-that-you-should-keep-it-super-super-secret'
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    app.app_context().push()

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.drop_all()
    db.create_all()
    if User.query.filter_by(username='admin').first() is None:
        user = User(username='admin',password='admin',is_admin=True)
        db.session.add(user)
        db.session.commit()
    if User.query.filter_by(username='user').first() is None:
        user = User(username='user',password='user',is_admin=False)
        db.session.add(user)
        db.session.commit()
    if not ParkingLot.query.first():
        lot1 = ParkingLot(name='IITM', address='guindy', pin_code=111, total_spots=5, price_per_hour=20)
        db.session.add(lot1)
        db.session.commit()
        for a in range(lot1.total_spots):
            new_spot = ParkingSpot(lot_id=lot1.id)
            db.session.add(new_spot)
        db.session.commit()


from application.auth import *
from application.admin import *
from application.user import *

@app.route('/')
def home():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)