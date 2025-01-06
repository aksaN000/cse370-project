from app import db
from datetime import datetime

class ConsultationSlot(db.Model):
    __tablename__ = 'ConsultationSlot'
    SlotID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Date = db.Column(db.Date, nullable=False)
    StartTime = db.Column(db.Time, nullable=False)
    EndTime = db.Column(db.Time, nullable=False)
    Status = db.Column(db.Text)
    HistoryID = db.Column(db.Integer, db.ForeignKey('ConsultationHistory.HistoryID'))
    NotificationID = db.Column(db.Integer, db.ForeignKey('Notification.NotificationID'))
    
    # Relationships
    offers = db.relationship('Offers', backref='slot', lazy=True)
    history = db.relationship('ConsultationHistory', backref='consultation_slots')
    bookings = db.relationship('Booking', backref='slot_booking', lazy=True)

class Offers(db.Model):
    __tablename__ = 'Offers'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    SlotID = db.Column(db.Integer, db.ForeignKey('ConsultationSlot.SlotID'), primary_key=True)
    ConsultationRoom = db.Column(db.Text)

class Booking(db.Model):
    __tablename__ = 'Booking'
    BookingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Purpose = db.Column(db.Text)
    BookingDate = db.Column(db.Date, nullable=False)
    BookingTime = db.Column(db.Time, nullable=False)
    BookingStatus = db.Column(db.Text)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'))
    SlotID = db.Column(db.Integer, db.ForeignKey('ConsultationSlot.SlotID'))
    
    # Define relationship with User
    user = db.relationship('User', backref='user_bookings')

class ConsultationHistory(db.Model):
    __tablename__ = 'ConsultationHistory'
    HistoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Notes = db.Column(db.Text)