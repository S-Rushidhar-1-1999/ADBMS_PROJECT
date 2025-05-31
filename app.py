from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import Database
from auth import login_required, admin_required, manager_required, check_employee_access
import os
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(hours=1)

# Inject current datetime into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Initialize database
db = Database()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db.verify_login(email, password)
        
        if user:
            session.permanent = True
            session['user_id'] = user['employee_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role_name']
            flash(f'Welcome {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user_role = session['user_role']
    
    if user_role == 'admin':
        employees = db.get_all_employees()
        return render_template('admin_dashboard.html', employees=employees)
    elif user_role == 'manager':
        employees = db.get_employees_by_role(3)  # role_id = 3 for employees
        return render_template('manager_dashboard.html', employees=employees)
    else:  # employee
        employee = db.get_employee_by_id(user_id)
        return render_template('employee_dashboard.html', employee=employee)

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    employee = db.get_employee_by_id(user_id)
    return render_template('profile.html', employee=employee)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = db.verify_login(session['user_email'], current_password)
        
        if not user:
            flash('Current password is incorrect', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        
        if db.update_password(session['user_id'], new_password):
            flash('Password updated successfully', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Failed to update password', 'error')
    
    return render_template('change_password.html')

# Admin routes
@app.route('/admin/add_employee', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        designation = request.form['designation']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        
        if db.add_employee(name, age, gender, address, phone_number, designation, email, password, role_id):
            flash('Employee added successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to add employee', 'error')
    
    return render_template('add_employee.html')

@app.route('/admin/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(employee_id):
    employee = db.get_employee_by_id(employee_id)
    
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        designation = request.form['designation']
        email = request.form['email']
        role_id = request.form['role_id']
        
        if db.update_employee(employee_id, name, age, gender, address, phone_number, designation, email, role_id):
            flash('Employee updated successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to update employee', 'error')
    
    return render_template('edit_employee.html', employee=employee)

@app.route('/admin/delete_employee/<int:employee_id>', methods=['POST'])
@login_required
@admin_required
def delete_employee(employee_id):
    if employee_id == session['user_id']:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('dashboard'))
    
    if db.delete_employee(employee_id):
        flash('Employee deleted successfully', 'success')
    else:
        flash('Failed to delete employee', 'error')
    
    return redirect(url_for('dashboard'))

# Manager routes
@app.route('/manager/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@manager_required
@check_employee_access
def manager_edit_employee(employee_id):
    employee = db.get_employee_by_id(employee_id)
    
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        
        if db.update_employee_limited(employee_id, name, age, gender, address, phone_number):
            flash('Employee updated successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to update employee', 'error')
    
    return render_template('manager_edit_employee.html', employee=employee)

if __name__ == '__main__':
    app.run(debug=True)
