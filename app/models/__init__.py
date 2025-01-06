from app import db
from .user import User, UserPhoneNum, Faculty, Student, ST, Admin
from .consultation import ConsultationSlot, Booking, ConsultationHistory, Offers
from .feedback import Feedback
from .notification import Notification, AdminDashboard
# Export all models
__all__ = [
    'User', 'UserPhoneNum', 'Faculty', 'Student', 'ST', 'Admin',
    'ConsultationSlot', 'Booking', 'ConsultationHistory', 'Offers',
    'Notification', 'AdminDashboard',
    'Feedback'
]