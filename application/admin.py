from application.models import *
from flask import current_app as app
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

# Show list of all lots
@app.route('/admin/lots', methods=['GET'])
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    return render_template('admindashboard.html', lots=parking_lots)



# Add a new parking lot
@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_lot():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            address = request.form.get('address')
            pin_code = int(request.form.get('pin_code'))
            total_spots = int(request.form.get('total_spots'))
            price_per_hour = float(request.form.get('price_per_hour'))

            if not name or not address or total_spots <= 0 or price_per_hour <= 0:
                flash('Invalid data provided. Please fill all fields correctly.', 'danger')
                return render_template('adminaddlot.html')

            new_lot = ParkingLot(name=name, address=address, pin_code=pin_code,
                                 total_spots=total_spots, price_per_hour=price_per_hour)
            db.session.add(new_lot)
            db.session.commit()

            for a in range(total_spots):
                db.session.add(ParkingSpot(lot_id=new_lot.id))

            db.session.commit()
            flash(f'Parking lot "{name}" added successfully!', 'success')
            return redirect('/admin/lots')

        except (KeyError, ValueError):
            flash('Invalid data provided. Please check your input.', 'danger')
            return render_template('adminaddlot.html')

    return render_template('adminaddlot.html')



# Edit an existing lot
@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if request.method == 'POST':
        price_per_hour_str = request.form.get('price_per_hour')
        new_total_spots_str = request.form.get('total_spots')

        if price_per_hour_str:
            try:
                lot.price_per_hour = float(price_per_hour_str)
            except (ValueError, TypeError):
                flash('Invalid price per hour value.', 'danger')
                return render_template('admineditlot.html', lot=lot)

        if new_total_spots_str:
            try:
                new_total_spots = int(new_total_spots_str)
            except (ValueError, TypeError):
                flash('Total spots must be a valid integer.', 'danger')
                return render_template('admineditlot.html', lot=lot)

            if new_total_spots < 0:
                flash('Total spots must be a positive number.', 'danger')
                return render_template('admineditlot.html', lot=lot)

            old_total_spots = lot.total_spots

            if new_total_spots > old_total_spots:
                for a in range(new_total_spots - old_total_spots):
                    db.session.add(ParkingSpot(lot_id=lot.id))
                    total_spots_left = lot.total_spots_left + 1
                lot.total_spots = new_total_spots

            elif new_total_spots < old_total_spots:
                occupied_spots_count = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=True).count()

                if new_total_spots < occupied_spots_count:
                    flash(f'Cannot reduce total spots to {new_total_spots} as {occupied_spots_count} spots are currently occupied.', 'danger')
                    return render_template('admineditlot.html', lot=lot)

                free_spots_to_delete = ParkingSpot.query.filter_by(
                    lot_id=lot.id, is_occupied=False
                ).order_by(ParkingSpot.id.desc()).limit(old_total_spots - new_total_spots).all()

                for spot in free_spots_to_delete:
                    db.session.delete(spot)

                lot.total_spots_left = new_total_spots
                lot.total_spots = new_total_spots

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect('/admin/lots')

    return render_template('admineditlot.html', lot=lot)



@app.route('/admin/delete/<int:lot_id>', methods=['GET','POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get(lot_id)

    if any(spot.is_occupied for spot in lot.spots):
        flash(f'Cannot delete lot "{lot.name}" because it has occupied spots.', 'danger')
        return redirect('/admin/lots')

    try:
        db.session.delete(lot)
        db.session.commit()
        flash(f'Parking lot "{lot.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect('/admin/lots')



@app.route('/admin/get_occupied_spots/<int:lot_id>', methods=['GET']) # Changed to GET for direct link
@login_required
def get_occupied_spots_with_details(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.', 'danger')
        return redirect(url_for('admin_dashboard')) # Redirect if lot not found

    occupied_spots_data = (
        db.session.query(
            Reservation.vehicle_number,
            User.username,
            Reservation.payment_status,
            Reservation.start_time,
            Reservation.end_time,
            Reservation.spot_id
        )
        .join(User, Reservation.user_id == User.id)
        .join(ParkingSpot, Reservation.spot_id == ParkingSpot.id)
        .filter(
            Reservation.lot_id == lot_id,
            ParkingSpot.is_occupied == True
        )
        .all()
    )

    # Format data for rendering
    result = []
    for vehicle_num, username, payment_status, start_time, end_time, spot_id in occupied_spots_data:
        result.append({
            "vehicle_number": vehicle_num,
            "username": username,
            "payment_status": payment_status.capitalize(),
            "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else 'N/A',
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'N/A',
            "spot_id": spot_id
        })
    
    if not result:
        flash(f'No occupied spots found for lot "{lot.name}".', 'info')
        # You can choose to redirect back to admin_dashboard or render the current page with no data
        # For this case, I'll render adminspots.html but with an empty table and the flash message
        # return redirect(url_for('admin_dashboard')) # Alternative: redirect back to dashboard
    
    return render_template('adminspots.html', lot_name=lot.name, occupied_spots=result)



@app.route('/admin/user_history', methods=['GET'])
def admin_user_history():
    all_users = User.query.filter_by(is_admin=False).all()
    return render_template('adminuserhistory.html', users=all_users)
