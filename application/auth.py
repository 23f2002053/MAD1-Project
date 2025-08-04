from flask import current_app as app
from flask import render_template, request, redirect, url_for, flash
from application.models import db, User
from flask_login import login_user, logout_user, login_required

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect('/')
        
        new_user = User(
            username=username,
            password=password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully! You can now log in.', 'success')
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect('/register')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user=User.query.filter_by(username=username).first()
        if username=='admin' and password=='admin':
          login_user(user)
          return redirect('/admin/lots')

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect('/user/dashboard')
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')