import pymysql
import hashlib
from datetime import datetime
import traceback
import os

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_database_if_not_exists()
        self.connect(database='employee_access_control')
        self.create_tables()
        self.create_admin_if_not_exists()

    def connect(self, database=None):
        """Establish connection to MySQL database (optionally to a specific database)"""
        try:
            self.connection = pymysql.connect(
                host='localhost',
                user='root',
                password='Rushi',  # 🔒 Replace with os.getenv("MYSQL_PASSWORD")
                database=database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            print(f"Connected to MySQL{' database: ' + database if database else ''}")
        except pymysql.MySQLError as e:
            print("Error connecting to MySQL:")
            traceback.print_exc()
            exit(1)

    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist"""
        try:
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS employee_access_control")
            print("Database 'employee_access_control' checked/created.")
        except pymysql.MySQLError as e:
            print("Error creating database:")
            traceback.print_exc()
            exit(1)

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create roles table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    role_id INT PRIMARY KEY AUTO_INCREMENT,
                    role_name VARCHAR(20) NOT NULL UNIQUE
                )
            """)
            
            # Create employees table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    age INT,
                    gender VARCHAR(10),
                    address TEXT,
                    phone_number VARCHAR(20),
                    designation VARCHAR(50),
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles(role_id)
                )
            """)
            
            # Insert default roles if none exist
            self.cursor.execute("SELECT COUNT(*) as count FROM roles")
            if self.cursor.fetchone()['count'] == 0:
                self.cursor.execute("""
                    INSERT INTO roles (role_name) VALUES 
                    ('admin'), ('manager'), ('employee')
                """)
            
            self.connection.commit()
            print("Tables created and roles initialized.")
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error creating tables:")
            traceback.print_exc()

    def create_admin_if_not_exists(self):
        """Create default admin user if none exists"""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM employees WHERE role_id = 1")
            if self.cursor.fetchone()['count'] == 0:
                admin_password = self.hash_password("admin123")  # 🔐 Consider changing this default password
                self.cursor.execute("""
                    INSERT INTO employees 
                    (name, age, gender, address, phone_number, designation, email, password, role_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ("Admin User", 30, "Other", "Admin Office", "1234567890", "System Administrator",
                      "admin@company.com", admin_password, 1))
                self.connection.commit()
                print("Default admin user created.")
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error creating admin user:")
            traceback.print_exc()

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_login(self, email, password):
        """Verify user login credentials"""
        try:
            hashed_password = self.hash_password(password)
            self.cursor.execute("""
                SELECT e.*, r.role_name 
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                WHERE e.email = %s AND e.password = %s
            """, (email, hashed_password))
            return self.cursor.fetchone()
        except pymysql.MySQLError:
            print("Login verification error:")
            traceback.print_exc()
            return None

    def get_all_employees(self):
        """Retrieve all employees"""
        try:
            self.cursor.execute("""
                SELECT e.*, r.role_name 
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                ORDER BY e.employee_id
            """)
            return self.cursor.fetchall()
        except pymysql.MySQLError:
            print("Error retrieving employees:")
            traceback.print_exc()
            return []

    def get_employee_by_id(self, employee_id):
        """Get employee by ID"""
        try:
            self.cursor.execute("""
                SELECT e.*, r.role_name 
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                WHERE e.employee_id = %s
            """, (employee_id,))
            return self.cursor.fetchone()
        except pymysql.MySQLError:
            print("Error retrieving employee:")
            traceback.print_exc()
            return None

    def get_employees_by_role(self, role_id):
        """Get employees by role"""
        try:
            self.cursor.execute("""
                SELECT e.*, r.role_name 
                FROM employees e
                JOIN roles r ON e.role_id = r.role_id
                WHERE e.role_id = %s
                ORDER BY e.employee_id
            """, (role_id,))
            return self.cursor.fetchall()
        except pymysql.MySQLError:
            print("Error retrieving employees by role:")
            traceback.print_exc()
            return []

    def add_employee(self, name, age, gender, address, phone_number, designation, email, password, role_id):
        """Add a new employee"""
        try:
            hashed_password = self.hash_password(password)
            self.cursor.execute("""
                INSERT INTO employees 
                (name, age, gender, address, phone_number, designation, email, password, role_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, age, gender, address, phone_number, designation, email, hashed_password, role_id))
            self.connection.commit()
            return True
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error adding employee:")
            traceback.print_exc()
            return False

    def update_employee(self, employee_id, name, age, gender, address, phone_number, designation, email, role_id):
        """Update full employee info"""
        try:
            self.cursor.execute("""
                UPDATE employees
                SET name = %s, age = %s, gender = %s, address = %s, phone_number = %s, 
                    designation = %s, email = %s, role_id = %s
                WHERE employee_id = %s
            """, (name, age, gender, address, phone_number, designation, email, role_id, employee_id))
            self.connection.commit()
            return True
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error updating employee:")
            traceback.print_exc()
            return False

    def update_employee_limited(self, employee_id, name, age, gender, address, phone_number):
        """Limited update (e.g. for manager role)"""
        try:
            self.cursor.execute("""
                UPDATE employees
                SET name = %s, age = %s, gender = %s, address = %s, phone_number = %s
                WHERE employee_id = %s
            """, (name, age, gender, address, phone_number, employee_id))
            self.connection.commit()
            return True
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error updating limited employee info:")
            traceback.print_exc()
            return False

    def update_password(self, employee_id, new_password):
        """Update password securely"""
        try:
            hashed_password = self.hash_password(new_password)
            self.cursor.execute("""
                UPDATE employees
                SET password = %s
                WHERE employee_id = %s
            """, (hashed_password, employee_id))
            self.connection.commit()
            return True
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error updating password:")
            traceback.print_exc()
            return False

    def delete_employee(self, employee_id):
        """Delete an employee by ID"""
        try:
            self.cursor.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
            self.connection.commit()
            return True
        except pymysql.MySQLError:
            self.connection.rollback()
            print("Error deleting employee:")
            traceback.print_exc()
            return False

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
