from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User, Faculty, Student, ST
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.Role == 'student':
            return redirect(url_for('dashboard.student'))
        elif current_user.Role == 'faculty':
            return redirect(url_for('dashboard.faculty'))
        elif current_user.Role == 'st':
            return redirect(url_for('dashboard.st'))
        else:
            return redirect(url_for('dashboard.admin'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(Email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # Redirect based on role
            if user.Role == 'student':
                return redirect(url_for('dashboard.student'))
            elif user.Role == 'faculty':
                return redirect(url_for('dashboard.faculty'))
            elif user.Role == 'st':
                return redirect(url_for('dashboard.st'))
            else:
                return redirect(url_for('dashboard.admin'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if user already exists
        if User.query.filter_by(Email=email).first():
            flash('Email already registered. Please login or use a different email.', 'error')
            return redirect(url_for('auth.register'))
            
        try:
            # Create user
            user = User(
                Name=name,
                Email=email,
                Role=role
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Get UserID
            
            # Create role-specific profile
            if role == 'faculty':
                faculty = Faculty(
                    UserID=user.UserID,
                    Department=request.form.get('department', ''),
                    Designation=request.form.get('designation', ''),
                    Office_Hour=request.form.get('office_hour', ''),
                    Desk_Num=request.form.get('desk_num', ''),
                    CourseDetails=request.form.get('course_details', ''),
                    Consultation_Hour=request.form.get('consultation_hour', '')
                )
                db.session.add(faculty)
                
            elif role == 'student':
                student = Student(
                    UserID=user.UserID,
                    Department=request.form.get('department', ''),
                    CourseDetails=request.form.get('course_details', '')
                )
                db.session.add(student)
                
            elif role == 'st':
                st = ST(
                    UserID=user.UserID,
                    Consultation_Hour=request.form.get('consultation_hour', ''),
                    Room_No=request.form.get('room_no', '')
                )
                db.session.add(st)
            
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Registration error: {str(e)}")  # For debugging
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.Role == 'student':
        return render_template('dashboard/student/profile.html', 
                             student=Student.query.get(current_user.UserID))
    elif current_user.Role == 'faculty':
        return render_template('dashboard/faculty/profile.html', 
                             faculty=Faculty.query.get(current_user.UserID))
    elif current_user.Role == 'st':
        return render_template('dashboard/st/profile.html', 
                             st=ST.query.get(current_user.UserID))
    else:
        return redirect(url_for('main.index'))

# Password reset functionality could be added here