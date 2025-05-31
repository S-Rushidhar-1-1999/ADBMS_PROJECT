from flask import session, redirect, url_for, flash
from functools import wraps

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager or admin role for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or (session['user_role'] != 'manager' and session['user_role'] != 'admin'):
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def check_employee_access(f):
    """Decorator to check if user has access to employee data"""
    @wraps(f)
    def decorated_function(employee_id, *args, **kwargs):
        # Admin can access any employee
        if session.get('user_role') == 'admin':
            return f(employee_id, *args, **kwargs)
        
        # Manager can access employees but not other managers or admins
        if session.get('user_role') == 'manager':
            from app import db
            employee = db.get_employee_by_id(employee_id)
            if employee and employee['role_name'] == 'employee':
                return f(employee_id, *args, **kwargs)
            else:
                flash('You do not have permission to access this employee', 'error')
                return redirect(url_for('dashboard'))
        
        # Employee can only access their own data
        if session.get('user_id') == int(employee_id):
            return f(employee_id, *args, **kwargs)
        else:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
    
    return decorated_function