from flask import Blueprint, app, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.consultation import ConsultationSlot, Booking, Offers
from app.models.notification import Notification
from app.models.user import User
from datetime import datetime, date
import logging
from sqlalchemy import or_, and_
# Configure logging
logger = logging.getLogger(__name__)

consultation = Blueprint('consultation', __name__)

@consultation.route('/bookings')
@login_required
def bookings():
    """
    Route to view user's bookings based on their role
    """
    if current_user.Role == 'student':
        # Students see their own bookings
        bookings = Booking.query.filter_by(UserID=current_user.UserID) \
            .join(ConsultationSlot) \
            .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
            .all()
        template = 'consultation/student_bookings.html'
    
    elif current_user.Role in ['faculty', 'st']:
        # Faculty/ST see bookings for their slots
        offers = Offers.query.filter_by(UserID=current_user.UserID).all()
        slot_ids = [offer.SlotID for offer in offers]
        bookings = Booking.query.filter(Booking.SlotID.in_(slot_ids)) \
            .join(ConsultationSlot) \
            .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
            .all()
        template = 'consultation/faculty_bookings.html'
    
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.index'))

    return render_template(template, bookings=bookings)

# Faculty: View and create consultation slots
@consultation.route('/faculty/schedule', methods=['GET', 'POST'])
@login_required
def faculty_schedule():
    """Handle faculty schedule view"""
    if current_user.Role != 'faculty':
        flash('Only faculty members can access this schedule page', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        room = request.form.get('room')
        
        try:
            slot = ConsultationSlot(
                Date=datetime.strptime(date, '%Y-%m-%d').date(),
                StartTime=datetime.strptime(start_time, '%H:%M').time(),
                EndTime=datetime.strptime(end_time, '%H:%M').time(),
                Status='available'
            )
            db.session.add(slot)
            db.session.flush()
            
            offer = Offers(
                UserID=current_user.UserID,
                SlotID=slot.SlotID,
                ConsultationRoom=room
            )
            
            db.session.add(offer)
            db.session.commit()
            flash('Consultation slot scheduled successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Error scheduling consultation slot.', 'error')
            logger.error(f'Error scheduling slot: {str(e)}')
        
    # Get user's scheduled slots
    scheduled_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()
    
    return render_template('dashboard/faculty/schedule.html', slots=scheduled_slots)

@consultation.route('/st/schedule', methods=['GET', 'POST'])
@login_required
def st_schedule():
    if current_user.Role not in ['faculty', 'st']:
        flash('Only faculty and STs can schedule consultations', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        room = request.form.get('room')
        
        try:
            # Validate inputs
            if not all([date, start_time, end_time, room]):
                flash('All fields are required', 'error')
                return redirect(url_for('consultation.st_schedule'))

            # Parse and validate dates and times
            slot_date = datetime.strptime(date, '%Y-%m-%d').date()
            slot_start_time = datetime.strptime(start_time, '%H:%M').time()
            slot_end_time = datetime.strptime(end_time, '%H:%M').time()

            # Check for time validity
            if slot_start_time >= slot_end_time:
                flash('Start time must be before end time', 'error')
                return redirect(url_for('consultation.st_schedule'))

            # Check for existing slots
            existing_slot = ConsultationSlot.query.filter_by(
                Date=slot_date, 
                StartTime=slot_start_time, 
                EndTime=slot_end_time
            ).first()

            if existing_slot:
                flash('A slot with this exact time already exists', 'error')
                return redirect(url_for('consultation.st_schedule'))

            # Create slot with additional details
            slot = ConsultationSlot(
                Date=slot_date,
                StartTime=slot_start_time,
                EndTime=slot_end_time,
                Status='available',
                ScheduledBy=current_user.Name,  # Track who scheduled
                Room=room  # Store room number
            )
            db.session.add(slot)
            db.session.flush()
            
            # Create offers entry
            offer = Offers(
                UserID=current_user.UserID,
                SlotID=slot.SlotID,
                ConsultationRoom=room
            )
            
            db.session.add(offer)
            db.session.commit()
            flash('Consultation slot scheduled successfully!', 'success')
            
        except ValueError as ve:
            db.session.rollback()
            flash('Invalid date or time format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error scheduling consultation slot.', 'error')
            logger.error(f'Error scheduling slot: {str(e)}')
        
    # Get user's scheduled slots
    scheduled_slots = ConsultationSlot.query.join(Offers).filter(
        Offers.UserID == current_user.UserID
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()
    
    return render_template('consultation/schedule.html', slots=scheduled_slots)

@consultation.route('/slot/<int:slot_id>', methods=['GET'])
@login_required
def slot_details(slot_id):
    """
    Route to view detailed information about a specific consultation slot
    """
    slot = ConsultationSlot.query.get_or_404(slot_id)

    # Basic authorization 
    offers = Offers.query.filter_by(SlotID=slot_id).first()
    if not offers:
        flash('Slot not found', 'error')
        return redirect(url_for('main.index'))

    # Get bookings for this slot
    bookings = Booking.query.filter_by(SlotID=slot_id).all()

    return render_template('consultation/slot_details.html', 
                           slot=slot, 
                           bookings=bookings)

@consultation.route('/slot/delete/<int:slot_id>', methods=['POST'])
@login_required
def delete_slot(slot_id):
    """
    Route to delete a consultation slot
    """
    slot = ConsultationSlot.query.get_or_404(slot_id)

    # Authorization check
    offers = Offers.query.filter_by(SlotID=slot_id, UserID=current_user.UserID).first()
    if not offers and current_user.Role != 'admin':
        flash('You are not authorized to delete this slot', 'error')
        return redirect(url_for('main.index'))

    # Check if slot has any bookings
    existing_bookings = Booking.query.filter_by(SlotID=slot_id).all()
    if existing_bookings:
        flash('Cannot delete a slot with existing bookings', 'error')
        return redirect(url_for('consultation.slot_details', slot_id=slot_id))

    try:
        # Delete associated offers
        Offers.query.filter_by(SlotID=slot_id).delete()
        
        # Delete the slot
        db.session.delete(slot)
        db.session.commit()
        
        flash('Slot deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting slot', 'error')
        logger.error(f'Slot deletion error: {str(e)}')

    return redirect(url_for('consultation.st_schedule'))

@consultation.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if current_user.Role != 'student':
        flash('Only students can book consultations', 'error')
        return redirect(url_for('main.index'))
    
    # Get available slots with their offers
    available_slots = ConsultationSlot.query.join(Offers).filter(
        ConsultationSlot.Status == 'available',
        ConsultationSlot.Date >= date.today()
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()

    return render_template('consultation/book.html', 
                         available_slots=available_slots)


# Faculty: View and manage bookings for consultation slots
@consultation.route('/faculty/bookings')
@login_required
def faculty_bookings():
    """
    Route for faculty to view their consultation bookings
    Requires faculty role
    """
    if current_user.Role != 'faculty':
        flash('Only faculty can view bookings', 'error')
        return redirect(url_for('main.index'))

    # Get bookings for the faculty's slots with comprehensive filtering
    bookings = Booking.query.join(ConsultationSlot) \
        .filter(ConsultationSlot.FacultyID == current_user.faculty_info.FacultyID) \
        .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
        .all()
    
    return render_template('consultation/faculty_bookings.html', bookings=bookings)
# Student: View and book consultation slots
@consultation.route('/student/book', methods=['GET', 'POST'])
@login_required
def student_book():
    """
    Route for students to view and book available consultation slots
    Requires student role
    """
    if current_user.Role != 'student':
        flash('Only students can book consultations', 'error')
        return redirect(url_for('main.index'))

    # Filter and prepare available slots
    available_slots = ConsultationSlot.query.filter(
        ConsultationSlot.Status == 'available',
        ConsultationSlot.Date >= date.today()
    ).order_by(ConsultationSlot.Date, ConsultationSlot.StartTime).all()

    # Apply additional filters if provided
    department = request.args.get('department')
    faculty = request.args.get('faculty')
    slot_date = request.args.get('date')
    time_slot = request.args.get('time_slot')

    if department:
        available_slots = [slot for slot in available_slots if slot.user.Department == department]
    
    if faculty:
        available_slots = [slot for slot in available_slots if slot.FacultyID == faculty]
    
    if slot_date:
        try:
            filter_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
            available_slots = [slot for slot in available_slots if slot.Date == filter_date]
        except ValueError:
            flash('Invalid date format', 'error')
    
    if time_slot:
        # Implement time slot filtering logic
        pass

    # Get departments using the class method
    from app.models.user import User
    departments = User.get_departments()

    # Get all faculty users
    faculties = User.query.filter_by(Role='faculty').all()

    if request.method == 'POST':
        try:
            slot_id = request.form.get('slot_id')
            purpose = request.form.get('purpose')

            # Validate inputs
            if not slot_id or not purpose:
                raise ValueError('Slot ID and purpose are required')

            slot = ConsultationSlot.query.get_or_404(slot_id)

            # Additional slot availability checks
            if slot.Status != 'available':
                raise ValueError('This slot is no longer available')

            # Check for existing bookings
            existing_booking = Booking.query.filter_by(
                UserID=current_user.UserID, 
                SlotID=slot_id
            ).first()

            if existing_booking:
                raise ValueError('You have already booked this slot')

            # Create booking
            booking = Booking(
                Purpose=purpose,
                BookingDate=date.today(),
                BookingTime=datetime.now().time(),
                BookingStatus='pending',
                UserID=current_user.UserID,
                SlotID=slot_id
            )

            # Update slot status
            slot.Status = 'booked'

            # Create notification for faculty
            notification = Notification(
                Message=f'New booking request from {current_user.Name} for {slot.Date.strftime("%B %d, %Y")}',
                NotificationTime=datetime.now(),
                UserID=slot.FacultyID,
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
            logger.error(f"Booking error: {str(e)}")

    return render_template('consultation/book.html', 
                           available_slots=available_slots,
                           departments=departments,
                           faculties=faculties)
# Student: View booked consultations
@consultation.route('/student/bookings')
@login_required
def student_bookings():
    """
    Route for students to view their booked consultations
    Requires student role
    """
    if current_user.Role != 'student':
        return redirect(url_for('main.index'))

    # Get student's bookings with comprehensive ordering
    bookings = Booking.query.filter_by(UserID=current_user.UserID) \
        .join(ConsultationSlot) \
        .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
        .all()
    
    return render_template('consultation/bookings.html', bookings=bookings)

@consultation.route('/slot/cancel/<int:slot_id>', methods=['POST'])
@login_required
def cancel_slot(slot_id):
    """
    Route to cancel a consultation slot
    Allows cancellation only if no bookings exist
    """
    slot = ConsultationSlot.query.get_or_404(slot_id)

    # Authorization check
    offers = Offers.query.filter_by(SlotID=slot_id, UserID=current_user.UserID).first()
    if not offers and current_user.Role not in ['faculty', 'st', 'admin']:
        flash('You are not authorized to cancel this slot', 'error')
        return redirect(url_for('main.index'))

    # Check for existing bookings
    existing_bookings = Booking.query.filter_by(SlotID=slot_id).all()
    if existing_bookings:
        flash('Cannot cancel a slot with existing bookings', 'error')
        return redirect(url_for('consultation.slot_details', slot_id=slot_id))

    try:
        # Delete associated offers
        Offers.query.filter_by(SlotID=slot_id).delete()
        
        # Delete the slot
        db.session.delete(slot)
        db.session.commit()
        
        flash('Slot cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling slot', 'error')
        logger.error(f'Slot cancellation error: {str(e)}')

    # Redirect based on user role
    if current_user.Role == 'faculty':
        return redirect(url_for('consultation.faculty_schedule'))
    elif current_user.Role == 'st':
        return redirect(url_for('consultation.st_schedule'))
    else:
        return redirect(url_for('main.index'))

# Consultation history for both students and faculty
@consultation.route('/history')
@login_required
def history():
    """
    Route to view consultation booking history
    Supports both student and faculty roles
    """
    if current_user.Role == 'student':
        # Student sees their own bookings
        bookings = Booking.query.filter_by(UserID=current_user.UserID) \
            .join(ConsultationSlot) \
            .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
            .all()
    else:
        # Faculty sees bookings for their slots
        offers = Offers.query.filter_by(UserID=current_user.UserID).all()
        slot_ids = [offer.SlotID for offer in offers]
        bookings = Booking.query.filter(Booking.SlotID.in_(slot_ids)) \
            .join(ConsultationSlot) \
            .order_by(ConsultationSlot.Date.desc(), ConsultationSlot.StartTime.desc()) \
            .all()

    return render_template('consultation/history.html', bookings=bookings)

# Booking details for both students and faculty
@consultation.route('/details/<int:booking_id>')
@login_required
def booking_details(booking_id):
    """
    Route to view detailed information about a specific booking
    Requires authorization based on user role
    """
    booking = Booking.query.get_or_404(booking_id)

    # Strict authorization check
    if not (current_user.UserID == booking.UserID or 
            current_user.UserID == booking.slot.FacultyID):
        abort(403)  # Forbidden

    return render_template('consultation/details.html', booking=booking)