from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.consultation import Booking, ConsultationSlot, Offers, ConsultationHistory
from app.models.feedback import Feedback
from app.models.notification import Notification, AdminDashboard
from app.models.user import User, Faculty, Student, ST, Admin
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.utils.decorators import admin_required

dashboard = Blueprint('dashboard', __name__)

# Student Dashboard
@dashboard.route('/student')
@login_required
def student():
    if current_user.Role != 'student':
        flash('Access denied: Student access only')
        return redirect(url_for('main.index'))
    
    #student's information
    student_info = Student.query.filter_by(UserID=current_user.UserID).first()
    # Get today's consultations
    today_consultations = Booking.query.join(ConsultationSlot).filter(
        Booking.UserID == current_user.UserID,
        ConsultationSlot.Date == date.today(),
        Booking.BookingStatus.in_(['pending', 'confirmed'])
    ).order_by(ConsultationSlot.StartTime).all()
     #upcoming consultations
    upcoming_consultations = Booking.query.join(ConsultationSlot).filter(
        Booking.UserID == current_user.UserID,
        ConsultationSlot.Date > date.today(),
        Booking.BookingStatus.in_(['pending', 'confirmed'])
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()

    # upcoming bookings
    upcoming_bookings = Booking.query.join(ConsultationSlot).filter(
        Booking.UserID == current_user.UserID,
        ConsultationSlot.Date >= date.today(),
        Booking.BookingStatus.in_(['pending', 'confirmed'])
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()
    
    #recent consultation history
    past_consultations = Booking.query.join(ConsultationSlot).filter(
        Booking.UserID == current_user.UserID,
        Booking.BookingStatus == 'completed'
    ).order_by(ConsultationSlot.Date.desc()).limit(5).all()
    
    # pending feedback requests
    pending_feedback = Booking.query.join(ConsultationSlot).filter(
        Booking.UserID == current_user.UserID,
        Booking.BookingStatus == 'completed'
    ).outerjoin(ConsultationHistory).outerjoin(Feedback).filter(
        Feedback.FeedbackID == None
    ).all()
    
    #unread notifications
    notifications = Notification.query.filter_by(
        UserID=current_user.UserID,
        IsRead=0
    ).order_by(Notification.NotificationTime.desc()).limit(5).all()
    
    stats = {
        'total_consultations': Booking.query.filter_by(
            UserID=current_user.UserID,
            BookingStatus='completed'
        ).count(),
        'pending_bookings': Booking.query.filter_by(
            UserID=current_user.UserID,
            BookingStatus='pending'
        ).count(),
        'upcoming_consultations': len(upcoming_bookings),
        'feedback_pending': len(pending_feedback)
    }
    
    return render_template('dashboard/student/dashboard.html',
                        student=student_info,
                        today_consultations=today_consultations,
                        upcoming_consultations=upcoming_consultations,
                        upcoming_bookings=upcoming_bookings,
                        past_consultations=past_consultations,
                        notifications=notifications,
                        stats=stats,
                        pending_feedback=pending_feedback,
                        profile_info=student_info)

# Faculty Dashboard
@dashboard.route('/faculty')
@login_required
def faculty():
    if current_user.Role != 'faculty':
        flash('Access denied: Faculty access only')
        return redirect(url_for('main.index'))
    
    faculty_info = Faculty.query.filter_by(UserID=current_user.UserID).first()
    
    # Get today's consultations
    today_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID,
        ConsultationSlot.Date == date.today()
    ).order_by(ConsultationSlot.StartTime).all()
    
    # Get upcoming slots
    upcoming_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID,
        ConsultationSlot.Date > date.today(),
        ConsultationSlot.Date <= date.today() + timedelta(days=7)
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()
    
    # Get pending booking requests
    pending_bookings = Booking.query.join(ConsultationSlot).join(Offers).filter(
        Offers.UserID == current_user.UserID,
        Booking.BookingStatus == 'pending'
    ).all()
    
    # Calculate statistics
    stats = {
        'total_consultations': Booking.query.join(ConsultationSlot).join(Offers).filter(
            Offers.UserID == current_user.UserID,
            Booking.BookingStatus == 'completed'
        ).count(),
        'pending_requests': len(pending_bookings),
        'todays_consultations': len(today_slots),
        'upcoming_slots': len(upcoming_slots)
    }
    
    # Get latest feedback
    recent_feedback = Feedback.query.join(ConsultationHistory).join(ConsultationSlot).join(
        Offers
    ).filter(
        Offers.UserID == current_user.UserID
    ).order_by(Feedback.FeedbackSubmissionDate.desc()).limit(5).all()
    
    return render_template('dashboard/faculty/dashboard.html',
                         faculty=faculty_info,
                         today_slots=today_slots,
                         upcoming_slots=upcoming_slots,
                         pending_bookings=pending_bookings,
                         stats=stats,
                         recent_feedback=recent_feedback)

# ST Dashboard
@dashboard.route('/st')
@login_required
def st():
    if current_user.Role != 'st':
        flash('Access denied: ST access only')
        return redirect(url_for('main.index'))
    
    st_info = ST.query.filter_by(UserID=current_user.UserID).first()
    
    # Similar to faculty dashboard but with ST-specific modifications
    today_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID,
        ConsultationSlot.Date == date.today()
    ).order_by(ConsultationSlot.StartTime).all()
    
    upcoming_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID,
        ConsultationSlot.Date > date.today(),
        ConsultationSlot.Date <= date.today() + timedelta(days=7)
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()
    
    stats = {
        'total_consultations': Booking.query.join(ConsultationSlot).join(Offers).filter(
            Offers.UserID == current_user.UserID,
            Booking.BookingStatus == 'completed'
        ).count(),
        'todays_slots': len(today_slots),
        'upcoming_slots': len(upcoming_slots)
    }
    
    return render_template('dashboard/st/dashboard.html',
                         st=st_info,
                         today_slots=today_slots,
                         upcoming_slots=upcoming_slots,
                         stats=stats)

# Admin Dashboard
@dashboard.route('/admin')
@login_required
def admin():
    if current_user.Role != 'admin':
        flash('Access denied: Admin access only')
        return redirect(url_for('main.index'))
    
    admin_info = Admin.query.filter_by(UserID=current_user.UserID).first()
    
    # System statistics
    stats = {
        'total_users': User.query.count(),
        'total_faculty': Faculty.query.count(),
        'total_students': Student.query.count(),
        'total_st': ST.query.count(),
        'total_consultations': Booking.query.filter_by(BookingStatus='completed').count(),
        'pending_bookings': Booking.query.filter_by(BookingStatus='pending').count()
    }
    
    # Recent activities
    recent_bookings = Booking.query.order_by(Booking.BookingDate.desc()).limit(10).all()
    recent_users = User.query.order_by(User.UserID.desc()).limit(10).all()
    
    # Department statistics
    dept_stats = db.session.query(
        Faculty.Department,
        func.count(ConsultationSlot.SlotID).label('total_slots')
    ).join(User).join(Offers).join(ConsultationSlot).group_by(Faculty.Department).all()
    
    return render_template('dashboard/admin/dashboard.html',
                         admin=admin_info,
                         stats=stats,
                         recent_bookings=recent_bookings,
                         recent_users=recent_users,
                         dept_stats=dept_stats)

@dashboard.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    # Prepare data for monthly consultations
    monthly_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    monthly_data = [65, 59, 80, 81, 56, 55]

    # Prepare data for department distribution
    dept_labels = ['Computer Science', 'Mathematics', 'Physics', 'Chemistry']
    dept_data = [300, 200, 150, 100]

    # Prepare data for user activity
    activity_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    activity_data = [500, 600, 450, 700]

    # Prepare data for feedback distribution
    feedback_data = [10, 20, 30, 40, 50]  # Count of 1-5 star ratings

    return render_template('dashboard/admin/reports.html',
                         monthly_labels=monthly_labels,
                         monthly_data=monthly_data,
                         dept_labels=dept_labels,
                         dept_data=dept_data,
                         activity_labels=activity_labels,
                         activity_data=activity_data,
                         feedback_data=feedback_data)

from flask_login import login_required, current_user
from app.models.user import User, Student, ST

from flask_login import login_required, current_user
from app.models.user import User, Student, ST

@dashboard.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update basic user info
        current_user.Name = request.form.get('name')
        current_user.Email = request.form.get('email')

        # Update role-specific info
        if current_user.Role == 'student':
            student = Student.query.get(current_user.UserID)
            if student:
                student.Room_Number = request.form.get('room_number')
                student.Consultation_Hours = request.form.get('consultation_hours')
        elif current_user.Role == 'st':
            st = ST.query.get(current_user.UserID)
            if st:
                st.Room_Number = request.form.get('room_number')
                st.Consultation_Hours = request.form.get('consultation_hours')

        db.session.commit()
        flash('Profile updated successfully!', 'success')

    # Fetch the user's role-specific information
    if current_user.Role == 'student':
        student = Student.query.get(current_user.UserID)
        profile_info = student
    elif current_user.Role == 'st':
        st = ST.query.get(current_user.UserID)
        profile_info = st

    return render_template(f'dashboard/{current_user.Role}/profile.html', profile_info=profile_info)
@dashboard.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('dashboard/admin/users.html', users=users)

@dashboard.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_details(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.Name = request.form.get('name')
            user.Email = request.form.get('email')
            
            if user.Role == 'faculty':
                faculty = Faculty.query.get(user.UserID)
                if faculty:
                    faculty.Department = request.form.get('department')
                    faculty.Designation = request.form.get('designation')
            
            db.session.commit()
            flash('User updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating user.', 'error')
            
    return render_template('dashboard/admin/user_details.html', user=user)

# dashboard/routes.py

@dashboard.route('/student/book', methods=['GET', 'POST'])
@login_required
def student_book():
    if current_user.Role != 'student':
        flash('Only students can book consultations', 'error')
        return redirect(url_for('main.index'))

    available_slots = ConsultationSlot.query.filter(
        ConsultationSlot.Status == 'available',
        ConsultationSlot.Date >= date.today()
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()

    if request.method == 'POST':
        try:
            slot_id = request.form.get('slot_id')
            purpose = request.form.get('purpose')

            if not slot_id or not purpose:
                raise ValueError('Slot ID and purpose are required')

            slot = ConsultationSlot.query.get_or_404(slot_id)

            if slot.Status != 'available':
                raise ValueError('This slot is no longer available')

            existing_booking = Booking.query.filter_by(
                UserID=current_user.UserID, 
                SlotID=slot_id
            ).first()

            if existing_booking:
                raise ValueError('You have already booked this slot')

            # Find the faculty offering this slot
            offer = Offers.query.filter_by(SlotID=slot_id).first()
            if not offer:
                raise ValueError('No faculty found for this slot')

            booking = Booking(
                Purpose=purpose,
                BookingDate=date.today(),
                BookingTime=datetime.now().time(),
                BookingStatus='pending',
                UserID=current_user.UserID,
                SlotID=slot_id
            )

            slot.Status = 'booked'

            notification = Notification(
                Message=f'New booking request from {current_user.Name} for {slot.Date.strftime("%B %d, %Y")}',
                NotificationTime=datetime.now(),
                UserID=offer.UserID,  # Use the faculty's UserID from the Offers table
                IsRead=False
            )

            db.session.add(booking)
            db.session.add(notification)
            db.session.commit()

            flash('Booking request submitted successfully!', 'success')
            return redirect(url_for('dashboard.student'))

        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while booking. Please try again.', 'error')

    return render_template('consultation/book.html', available_slots=available_slots)