from flask import current_app as app
from flask import render_template, request, redirect, url_for, flash
from application.models import db, User, ParkingLot, ParkingSpot, Reservation, ParkingHistory
from flask_login import login_required, current_user
from datetime import datetime



@app.route('/user/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    user_id = current_user.id

    reservations_query = db.session.query(
        Reservation,
        ParkingLot,
        ParkingSpot
    ).join(
        ParkingLot,
        Reservation.lot_id == ParkingLot.id
    ).join(
        ParkingSpot,
        Reservation.spot_id == ParkingSpot.id
    ).filter(
        Reservation.user_id == user_id
    ).order_by(Reservation.start_time.desc()).all()

    reservations_data = []
    for reservation, lot, spot in reservations_query:
        reservations_data.append({
            'id': reservation.id,
            'vehicle_number': reservation.vehicle_number,
            'start_time': reservation.start_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.start_time else 'N/A',
            'end_time': reservation.end_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.end_time else 'N/A',
            'price_per_hour': f"${reservation.price_per_hour:.2f}",
            'payment_status': reservation.payment_status.capitalize(),
            'lot_name': lot.name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'spot_number': spot.id
        })

    return render_template('user_dashboard.html', reservations=reservations_data)

@app.route('/user/history', methods=['GET'])
@login_required
def user_history():

    user_id = current_user.id
    history_query = ParkingHistory.query.filter_by(user_id=user_id).order_by(ParkingHistory.end_time.desc()).all()
    history_data = []
    for record in history_query:
        history_data.append({
            'id': record.id,
            'vehicle_number': record.vehicle_number,
            'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'price_per_hour': f"${record.price_per_hour:.2f}",
            'lot_name': record.lot_name,
            'pin_code': record.pin_code,
            'address': record.address
        })
    return render_template('user_history.html', history=history_data)


@app.route('/user/lots', methods=['GET'])
@login_required
def available_parking_lots():
    lots = ParkingLot.query.all()
    parking_lots_data = []
    for lot in lots:
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=True).count()
        total_spots_left = int(lot.total_spots) - int(occupied_spots)
        parking_lots_data.append({
            'id': lot.id,
            'name': lot.name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'total_spots_left': total_spots_left,
            'price_per_hour': f"${lot.price_per_hour:.2f}"
        })
    return render_template('available_lots.html', lots=parking_lots_data)



@app.route('/user/book/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def book_parking_spot(lot_id):


    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        user_id = current_user.id

        if not vehicle_number:
            flash('Please enter a vehicle number.', 'danger')
            return redirect(url_for('book_parking_spot', lot_id=lot_id))

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            flash('Invalid parking lot selected.', 'danger')
            return redirect(url_for('available_parking_lots'))

        spot = ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=False).first()
        if not spot:
            flash(f'No available parking spots in lot "{lot.name}".', 'danger')
            return redirect(url_for('available_parking_lots'))

    
        reservation = Reservation(
            user_id=user_id,
            vehicle_number=vehicle_number,
            price_per_hour=lot.price_per_hour,
            lot_id=lot_id,
            spot_id=spot.id,
            payment_status='bookedin' 
        )

       
        spot.is_occupied = True
        total_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
        lot.total_spots_left = total_spots - ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=True).count()

        db.session.add(reservation)
        db.session.commit()
        return redirect(url_for('user_dashboard'))

    
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash('Invalid parking lot.', 'danger')
        return redirect(url_for('available_parking_lots'))
    return render_template('book_spot.html', lot=lot)


@app.route('/user/park_in/<int:reservation_id>', methods=['POST'])
@login_required
def park_vehicle(reservation_id):
 
    user_id = current_user.id

    reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()

    if not reservation:
        flash('Reservation not found or does not belong to you.', 'danger')
        return redirect(url_for('user_dashboard'))

    if reservation.payment_status == 'parkedin':
        flash('Vehicle is already parked in.', 'info')
        return redirect(url_for('user_dashboard'))

  
    reservation.start_time = datetime.utcnow()
    reservation.payment_status = 'parkedin'
    db.session.commit()

    flash(f'Vehicle {reservation.vehicle_number} parked in at spot {reservation.spot_id}.', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/user/release/<int:reservation_id>', methods=['POST'])
@login_required
def release_parking_spot(reservation_id):
    """
    Releases a parking spot, moves the reservation to history, and calculates cost.
    """
    user_id = current_user.id

    reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()

    if reservation.payment_status != 'parkedin':
        flash('Vehicle must be parked in before it can be released.', 'warning')
        return redirect(url_for('user_dashboard'))

    spot = ParkingSpot.query.get(reservation.spot_id)
    lot = ParkingLot.query.get(reservation.lot_id)

    if not spot or not lot:
        flash('Associated parking spot or lot not found.', 'danger')
        return redirect(url_for('user_dashboard'))

    if not reservation.start_time:
        flash('Cannot release: Parking start time not recorded.', 'danger')
        return redirect(url_for('user_dashboard'))
    end_time = datetime.utcnow()

  
    history_record = ParkingHistory(
        user_id=user_id,
        vehicle_number=reservation.vehicle_number,
        start_time=reservation.start_time,
        end_time=end_time,
        price_per_hour=reservation.price_per_hour,
        lot_name=lot.name,
        pin_code=lot.pin_code,
        address=lot.address
    )
    db.session.add(history_record)

 
    spot.is_occupied = False
    db.session.delete(reservation) 
    db.session.commit() 

    return redirect(url_for('user_dashboard'))