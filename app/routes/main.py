from flask import Blueprint, render_template, request
from flask_login import current_user
from app.models.consultation import ConsultationSlot, Booking
from app.models.user import Faculty, ST
from datetime import datetime, date
from sqlalchemy import func
from flask import flash, redirect, url_for, jsonify
from app.models.user import User


main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.student' if current_user.Role == 'student' 
                              else 'dashboard.faculty' if current_user.Role == 'faculty'
                              else 'dashboard.st' if current_user.Role == 'st'
                              else 'dashboard.admin'))
    
    # Get statistics for landing page
    stats = {
        'total_consultations': Booking.query.filter_by(BookingStatus='completed').count(),
        'total_faculty': Faculty.query.count(),
        'total_st': ST.query.count(),
        'active_slots': ConsultationSlot.query.filter(
            ConsultationSlot.Date >= date.today(),
            ConsultationSlot.Status == 'available'
        ).count()
    }
    
    return render_template('main/index.html', stats=stats)

@main.route('/about')
def about():
    return render_template('main/about.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        try:
            # Here you could add code to send email or save contact message
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            flash('An error occurred. Please try again later.', 'error')
    
    return render_template('main/contact.html')

@main.route('/search')
def search():
    query = request.args.get('q', '')
    filter_type = request.args.get('type', 'faculty')
    
    if not query:
        return render_template('main/search.html', results=None)
    
    if filter_type == 'faculty':
        results = Faculty.query.join(User).filter(
            User.Name.ilike(f'%{query}%')
        ).all()
    else:
        results = ST.query.join(User).filter(
            User.Name.ilike(f'%{query}%')
        ).all()
    
    return render_template('main/search.html', results=results, query=query)

@main.route('/faq')
def faq():
    faqs = [
        {
            'question': 'How do I book a consultation?',
            'answer': 'Log in as a student, go to "Book Consultation" and select your preferred time slot.'
        },
        {
            'question': 'How can faculty set their availability?',
            'answer': 'Faculty members can set their availability through the Schedule page in their dashboard.'
        },
        {
            'question': 'What is an ST?',
            'answer': 'STs (Student Teachers) are graduate students who can also offer consultations in specific subjects.'
        },
        {
            'question': 'How do I cancel my booking?',
            'answer': 'You can cancel your booking through your dashboard up to 24 hours before the scheduled time.'
        }
    ]
    return render_template('main/faq.html', faqs=faqs)

@main.route('/terms')
def terms():
    return render_template('main/terms.html')

@main.route('/privacy')
def privacy():
    return render_template('main/privacy.html')

# Error handlers
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Utility endpoints
@main.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now()})

@main.context_processor
def utility_processor():
    def format_date(date):
        return date.strftime('%B %d, %Y')
        
    def format_time(time):
        return time.strftime('%I:%M %p')
        
    return dict(
        format_date=format_date,
        format_time=format_time
    )