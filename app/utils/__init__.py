from .decorators import admin_required, role_required
from .email import send_email, send_consultation_confirmation, send_consultation_reminder

# You can add any utility functions that need to be accessible throughout the app
def format_datetime(dt):
    """Utility function to format datetime objects"""
    if dt:
        return dt.strftime('%B %d, %Y %I:%M %p')
    return ''

def format_date(d):
    """Utility function to format date objects"""
    if d:
        return d.strftime('%B %d, %Y')
    return ''

def format_time(t):
    """Utility function to format time objects"""
    if t:
        return t.strftime('%I:%M %p')
    return ''

# Export the functions you want to make available
__all__ = [
    'admin_required',
    'role_required',
    'send_email',
    'send_consultation_confirmation',
    'send_consultation_reminder',
    'format_datetime',
    'format_date',
    'format_time'
]