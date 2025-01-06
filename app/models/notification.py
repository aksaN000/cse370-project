from app import db
from datetime import datetime

from app import db

from app import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'Notification'
    NotificationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Message = db.Column(db.Text, nullable=False)
    NotificationTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    IsRead = db.Column(db.Integer, default=0)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'))
    
    # Using a different backref name
    consultation_slots = db.relationship('ConsultationSlot', backref='slot_notification', lazy=True)

    def __repr__(self):
        return f'<Notification {self.NotificationID}>'

class AdminDashboard(db.Model):
    __tablename__ = 'AdminDashboard'
    DashboardID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ActivityLog = db.Column(db.Text)
    
    # Relationship with Admin
    admins = db.relationship('Admin', backref='admin_dashboard')
    
    def log_activity(self, activity):
        """Add a new activity to the log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_log = f'[{timestamp}] {activity}'
        
        if self.ActivityLog:
            self.ActivityLog = new_log + '\n' + self.ActivityLog
        else:
            self.ActivityLog = new_log