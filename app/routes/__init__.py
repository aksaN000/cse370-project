from flask import Blueprint
from .main import main
from .auth import auth
from .consultation import consultation
from .dashboard import dashboard
from .feedback import feedback
from .notifications import notifications

# Define prefixes for routes if needed
# auth.url_prefix = '/auth'
# dashboard.url_prefix = '/dashboard'
# consultation.url_prefix = '/consultation'
# feedback.url_prefix = '/feedback'
# notifications.url_prefix = '/notifications'

# List all blueprints for easy import
blueprints = [
    main,
    auth,
    consultation,
    dashboard,
    feedback,
    notifications
]

# Export the blueprints you want to make available
__all__ = [
    'main',
    'auth',
    'consultation',
    'dashboard',
    'feedback',
    'notifications'
]