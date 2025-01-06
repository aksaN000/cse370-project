from app import db
from datetime import date

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    FeedbackID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Rating = db.Column(db.Integer)
    Comment = db.Column(db.Text)
    SubmittedBy = db.Column(db.Integer, db.ForeignKey('User.UserID'))
    FeedbackSubmissionDate = db.Column(db.Date, nullable=False, default=date.today)
    HistoryID = db.Column(db.Integer, db.ForeignKey('ConsultationHistory.HistoryID'))
    
    # Define relationships
    submitted_by_user = db.relationship('User', backref='feedbacks_given', 
                                      foreign_keys=[SubmittedBy])
    consultation_history = db.relationship('ConsultationHistory', 
                                         backref='feedbacks')
    
    def __repr__(self):
        return f'<Feedback {self.FeedbackID}>'

    @property
    def formatted_date(self):
        return self.FeedbackSubmissionDate.strftime('%B %d, %Y')