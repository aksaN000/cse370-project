from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification
from datetime import datetime

notifications = Blueprint('notifications', __name__)

@notifications.route('/')
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(
        UserID=current_user.UserID
    ).order_by(Notification.NotificationTime.desc()).all()
    
    unread_count = Notification.query.filter_by(
        UserID=current_user.UserID,
        IsRead=0
    ).count()
    
    return render_template('notifications/list.html', 
                         notifications=notifications,
                         unread_count=unread_count)

@notifications.route('/mark-read/<int:notification_id>')
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.UserID != current_user.UserID:
        return redirect(url_for('notifications.list_notifications'))
        
    notification.IsRead = 1
    db.session.commit()
    return redirect(url_for('notifications.list_notifications'))

@notifications.route('/mark-all-read')
@login_required
def mark_all_read():
    Notification.query.filter_by(
        UserID=current_user.UserID,
        IsRead=0
    ).update({Notification.IsRead: 1})
    
    db.session.commit()
    return redirect(url_for('notifications.list_notifications'))