from flask import current_app
from flask_mail import Message, Mail
from threading import Thread
from app import db
from app.models.notification import Notification
from datetime import datetime

mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

def send_email(subject, recipients, text_body, html_body=None):
    """
    Send email wrapper that handles the email sending asynchronously
    """
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=text_body,
        html=html_body
    )
    
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_consultation_confirmation(booking):
    """
    Send consultation confirmation email to both student and faculty/ST
    """
    # Student email
    student_subject = "Consultation Booking Confirmation"
    student_body = f"""
    Dear {booking.user.Name},

    Your consultation has been confirmed for:
    Date: {booking.slot.Date.strftime('%B %d, %Y')}
    Time: {booking.slot.StartTime.strftime('%I:%M %p')} - {booking.slot.EndTime.strftime('%I:%M %p')}
    With: {booking.slot.offers[0].user.Name}
    Location: {booking.slot.offers[0].ConsultationRoom}

    Purpose: {booking.Purpose}

    Please arrive on time. If you need to cancel, please do so at least 24 hours in advance.

    Best regards,
    Consultation Manager Team
    """
    
    send_email(
        subject=student_subject,
        recipients=[booking.user.Email],
        text_body=student_body
    )

    # Faculty/ST email
    faculty_subject = "New Consultation Booking"
    faculty_body = f"""
    Dear {booking.slot.offers[0].user.Name},

    A new consultation has been booked:
    Student: {booking.user.Name}
    Date: {booking.slot.Date.strftime('%B %d, %Y')}
    Time: {booking.slot.StartTime.strftime('%I:%M %p')} - {booking.slot.EndTime.strftime('%I:%M %p')}
    Location: {booking.slot.offers[0].ConsultationRoom}

    Purpose: {booking.Purpose}

    Best regards,
    Consultation Manager Team
    """
    
    send_email(
        subject=faculty_subject,
        recipients=[booking.slot.offers[0].user.Email],
        text_body=faculty_body
    )

def send_consultation_reminder(booking):
    """
    Send reminder emails 24 hours before consultation
    """
    # Student reminder
    student_subject = "Consultation Reminder"
    student_body = f"""
    Dear {booking.user.Name},

    This is a reminder for your consultation tomorrow:
    Time: {booking.slot.StartTime.strftime('%I:%M %p')} - {booking.slot.EndTime.strftime('%I:%M %p')}
    With: {booking.slot.offers[0].user.Name}
    Location: {booking.slot.offers[0].ConsultationRoom}

    Best regards,
    Consultation Manager Team
    """
    
    send_email(
        subject=student_subject,
        recipients=[booking.user.Email],
        text_body=student_body
    )

def send_cancellation_notification(booking, cancelled_by):
    """
    Send cancellation notification to affected party
    """
    if cancelled_by == 'student':
        recipient = booking.slot.offers[0].user
        subject = "Consultation Cancelled by Student"
        body = f"""
        Dear {recipient.Name},

        The consultation scheduled for {booking.slot.Date.strftime('%B %d, %Y')} at 
        {booking.slot.StartTime.strftime('%I:%M %p')} has been cancelled by the student.

        Student: {booking.user.Name}

        The slot has been made available again.

        Best regards,
        Consultation Manager Team
        """
    else:
        recipient = booking.user
        subject = "Consultation Cancelled by Faculty/ST"
        body = f"""
        Dear {recipient.Name},

        Unfortunately, your consultation scheduled for {booking.slot.Date.strftime('%B %d, %Y')} at 
        {booking.slot.StartTime.strftime('%I:%M %p')} has been cancelled.

        Please book another consultation slot.

        Best regards,
        Consultation Manager Team
        """
    
    send_email(
        subject=subject,
        recipients=[recipient.Email],
        text_body=body
    )
    
    # Create notification in system
    notification = Notification(
        Message=f"Consultation on {booking.slot.Date.strftime('%B %d, %Y')} has been cancelled.",
        NotificationTime=datetime.now(),
        UserID=recipient.UserID,
        IsRead=0
    )
    db.session.add(notification)
    db.session.commit()