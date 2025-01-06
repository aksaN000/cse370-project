from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.feedback import Feedback
from app.models.consultation import ConsultationHistory, ConsultationSlot, Booking, Offers
from app.models.notification import Notification
from datetime import datetime

feedback = Blueprint('feedback', __name__)

@feedback.route('/create/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def create_feedback(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify if user is authorized to give feedback
    if not (current_user.UserID == booking.UserID or 
            current_user.UserID == booking.slot.offers[0].UserID):
        flash('You are not authorized to provide feedback for this consultation')
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        # Create consultation history if not exists
        history = booking.slot.history
        if not history:
            history = ConsultationHistory(Notes='')
            db.session.add(history)
            db.session.flush()
            booking.slot.HistoryID = history.HistoryID
            
        # Create feedback
        feedback = Feedback(
            Rating=rating,
            Comment=comment,
            SubmittedBy=current_user.UserID,
            FeedbackSubmissionDate=datetime.now().date(),
            HistoryID=history.HistoryID
        )
        
        try:
            db.session.add(feedback)
            
            # Create notification for the other party
            recipient_id = booking.UserID if current_user.UserID != booking.UserID else booking.slot.offers[0].UserID
            notification = Notification(
                Message=f"New feedback received for consultation on {booking.slot.Date.strftime('%B %d, %Y')}",
                NotificationTime=datetime.now(),
                UserID=recipient_id,
                IsRead=0
            )
            db.session.add(notification)
            
            db.session.commit()
            flash('Feedback submitted successfully!')
            
            if current_user.Role == 'student':
                return redirect(url_for('dashboard.student'))
            else:
                return redirect(url_for('dashboard.faculty'))
                
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting feedback')
            
    return render_template('feedback/create.html', booking=booking)

@feedback.route('/view/<int:booking_id>')
@login_required
def view_feedback(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify if user is authorized to view feedback
    if not (current_user.UserID == booking.UserID or 
            current_user.UserID == booking.slot.offers[0].UserID):
        flash('You are not authorized to view this feedback')
        return redirect(url_for('main.index'))
        
    feedbacks = []
    if booking.slot.history:
        feedbacks = Feedback.query.filter_by(HistoryID=booking.slot.history.HistoryID).all()
    
    return render_template('feedback/view.html', booking=booking, feedbacks=feedbacks)

# feedback/routes.py

@feedback.route('/my-feedback')
@login_required
def my_feedback():
    if current_user.Role == 'student':
        # Get feedback for student's consultations
        feedbacks_received = Feedback.query.join(ConsultationHistory).join(
            Booking, Booking.SlotID == ConsultationHistory.SlotID
        ).filter(Booking.UserID == current_user.UserID).all()
        
        feedbacks_given = Feedback.query.filter_by(
            SubmittedBy=current_user.UserID
        ).all()
        
    else:
        # Get feedback for faculty/ST's consultations
        feedbacks_received = Feedback.query.join(ConsultationHistory).join(
            Booking, Booking.SlotID == ConsultationHistory.SlotID
        ).join(Offers).filter(Offers.UserID == current_user.UserID).all()
        
        feedbacks_given = Feedback.query.filter_by(
            SubmittedBy=current_user.UserID
        ).all()
    
    return render_template('feedback/my_feedback.html', 
                           feedbacks_received=feedbacks_received,
                           feedbacks_given=feedbacks_given)