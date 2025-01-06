from app import create_app, db
from app.models.user import User, UserPhoneNum, Faculty, Student, ST, Admin
from app.models.consultation import ConsultationSlot, Booking, ConsultationHistory, Offers
from app.models.feedback import Feedback
from app.models.notification import Notification, AdminDashboard

app = create_app()

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables.")

        # Create all tables
        db.create_all()
        print("Created all tables.")

if __name__ == "__main__":
    init_db()