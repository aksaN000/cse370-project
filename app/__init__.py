from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Config class definition
class Config:
    SECRET_KEY = '123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///consultation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

def configure_logging(app):
    """Configure application logging"""
    log_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    
    log_path = os.path.join(log_dir, 'consultation_app.log')
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=10240,
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    
    logger = logging.getLogger('consultation_app')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    logger.addHandler(console_handler)
    
    app.logger = logger
    app.logger.info('Consultation Management Application startup')

def register_error_handlers(app):
    """Register custom error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Not Found: {error}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.error(f'Forbidden Access: {error}')
        return render_template('errors/403.html'), 403

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Configure logging
    configure_logging(app)

    # Register blueprints
    from .routes.main import main
    from .routes.auth import auth
    from .routes.consultation import consultation
    from .routes.dashboard import dashboard
    from .routes.feedback import feedback
    from .routes.notifications import notifications

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(consultation)
    app.register_blueprint(dashboard)
    app.register_blueprint(feedback)
    app.register_blueprint(notifications)

    # Register error handlers
    register_error_handlers(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))

    # Shell context processor
    @app.shell_context_processor
    def make_shell_context():
        from .models.user import User
        from .models.consultation import ConsultationSlot
        from .models.notification import Notification
        from .models.feedback import Feedback
        return {
            'db': db,
            'User': User,
            'ConsultationSlot': ConsultationSlot,
            'Notification': Notification,
            'Feedback': Feedback,
        }

    return app

# Import models to avoid circular imports
from .models.user import User
from .models.consultation import ConsultationSlot
from .models.notification import Notification
from .models.feedback import Feedback