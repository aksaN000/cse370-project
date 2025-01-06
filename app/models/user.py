from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'User'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    Password = db.Column(db.Text, nullable=False)
    Role = db.Column(db.Text, nullable=False)
    @classmethod
    def get_departments(cls):
        return db.session.query(Faculty.Department).distinct().all()
    # Relationships
    phone_numbers = db.relationship('UserPhoneNum', backref='user', lazy=True)
    faculty_info = db.relationship('Faculty', backref='user_faculty', uselist=False, lazy=True)
    student_info = db.relationship('Student', backref='user_student', uselist=False, lazy=True)
    st_info = db.relationship('ST', backref='user_st', uselist=False, lazy=True)
    admin_info = db.relationship('Admin', backref='user_admin', uselist=False, lazy=True)
    notifications = db.relationship('Notification', backref='notification_user', lazy=True)
    offers = db.relationship('Offers', backref='offering_user', lazy=True)
    bookings = db.relationship('Booking', backref='booking_user', lazy=True)

    def get_id(self):
        return str(self.UserID)

    def set_password(self, password):
        self.Password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password, password)

class UserPhoneNum(db.Model):
    __tablename__ = 'User_Phone_Num'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    Phone_Num = db.Column(db.Text, primary_key=True)

class Faculty(db.Model):
    __tablename__ = 'Faculty'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    CourseDetails = db.Column(db.Text)
    Department = db.Column(db.Text)
    Designation = db.Column(db.Text)
    Office_Hour = db.Column(db.Text)
    Desk_Num = db.Column(db.Text)
    Consultation_Hour = db.Column(db.Text)
    
    # Access consultation slots through user's offers
    consultation_slots = db.relationship(
        'ConsultationSlot',
        secondary='Offers',
        primaryjoin='and_(Faculty.UserID == User.UserID, User.UserID == Offers.UserID)',
        secondaryjoin='Offers.SlotID == ConsultationSlot.SlotID',
        backref=db.backref('faculty', lazy=True),
        lazy='dynamic',
        viewonly=True
    )

class Student(db.Model):
    __tablename__ = 'Student'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    Department = db.Column(db.Text)
    CourseDetails = db.Column(db.Text)

class ST(db.Model):
    __tablename__ = 'ST'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    Consultation_Hour = db.Column(db.Text)
    Room_No = db.Column(db.Text)
    
    # Access consultation slots through user's offers
    consultation_slots = db.relationship(
        'ConsultationSlot',
        secondary='Offers',
        primaryjoin='and_(ST.UserID == User.UserID, User.UserID == Offers.UserID)',
        secondaryjoin='Offers.SlotID == ConsultationSlot.SlotID',
        backref=db.backref('st', lazy=True),
        lazy='dynamic',
        viewonly=True
    )

class Admin(db.Model):
    __tablename__ = 'Admin'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    Access_Level = db.Column(db.Text)
    DashboardID = db.Column(db.Integer, db.ForeignKey('AdminDashboard.DashboardID'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))