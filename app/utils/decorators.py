from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access based on user roles.
    Usage: @role_required('admin', 'faculty')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            if current_user.Role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator specifically for admin-only routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.Role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def consultation_owner_required(f):
    """
    Decorator to check if user owns/is part of the consultation
    To be used with routes that have consultation_id parameter
    """
    @wraps(f)
    def decorated_function(consultation_id, *args, **kwargs):
        from app.models.consultation import ConsultationSlot, Booking
        
        slot = ConsultationSlot.query.get_or_404(consultation_id)
        if current_user.Role == 'student':
            booking = Booking.query.filter_by(
                SlotID=consultation_id,
                UserID=current_user.UserID
            ).first()
            if not booking:
                flash('You do not have access to this consultation.', 'error')
                return redirect(url_for('main.index'))
        elif current_user.Role in ['faculty', 'st']:
            if not any(offer.UserID == current_user.UserID for offer in slot.offers):
                flash('You do not have access to this consultation.', 'error')
                return redirect(url_for('main.index'))
        return f(consultation_id, *args, **kwargs)
    return decorated_function

def prevent_authenticated(f):
    """
    Decorator to prevent authenticated users from accessing certain routes
    (like login and register pages)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function