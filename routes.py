from flask import Blueprint, request, jsonify
from models import db, User, Notification
from notification_service import NotificationService
from rabbitmq_producer import publish_notification

routes = Blueprint('routes', __name__)

@routes.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data or not all(key in data for key in ['name', 'email']):
        return jsonify({'error': 'Missing required fields'}), 400

    user = User(name=data['name'], email=data['email'], phone=data.get('phone', ''))
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone
    }), 201

@routes.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone
    } for user in users]), 200

@routes.route('/notifications', methods=['POST'])
def send_notification():
    data = request.json
    if not data or not all(key in data for key in ['user_id', 'type', 'title', 'content']):
        return jsonify({'error': 'Missing required fields'}), 400

    user = db.session.get(User, data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    notification_type = data['type'].lower()
    if notification_type not in ['email', 'sms', 'in-app']:
        return jsonify({'error': 'Invalid notification type'}), 400

    notification = Notification(
        user_id=user.id,
        type=notification_type,
        title=data['title'],
        content=data['content']
    )
    db.session.add(notification)
    db.session.commit()

    # Create queue data
    queue_data = {
        "notification_id": notification.id,
        "user_id": user.id,
        "email": user.email,
        "phone": user.phone,
        "type": notification_type,
        "title": data['title'],
        "content": data['content']
    }

    success_msg = "Notification enqueued for processing."
    
    # If it's an in-app notification, send it directly without RabbitMQ
    if notification_type == 'in-app':
        success, message = NotificationService.send_in_app_notification(
            user.id, 
            data['title'], 
            data['content']
        )
        if success:
            success_msg = "In-app notification sent directly."
        else:
            success_msg = f"Failed to send in-app notification: {message}"
    else:
        # Try to use RabbitMQ for email and SMS, but handle errors
        try:
            publish_notification(queue_data)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to publish to RabbitMQ: {str(e)}")
            success_msg = "Notification saved but queueing failed. RabbitMQ may be down."

    return jsonify({
        'id': notification.id,
        'user_id': notification.user_id,
        'type': notification.type,
        'title': notification.title,
        'content': notification.content,
        'timestamp': notification.timestamp,
        'message': success_msg,
        'success': True
    }), 201

@routes.route('/users/<int:user_id>/notifications', methods=['GET'])
def get_user_notifications(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    notification_type = request.args.get('type')
    read_status = request.args.get('read')
    query = Notification.query.filter_by(user_id=user_id)

    if notification_type:
        query = query.filter_by(type=notification_type)

    if read_status is not None:
        query = query.filter_by(read=read_status.lower() == 'true')

    notifications = query.order_by(Notification.timestamp.desc()).all()
    return jsonify([{
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'content': n.content,
        'timestamp': n.timestamp.isoformat(),
        'read': n.read
    } for n in notifications]), 200

@routes.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    notification = db.session.get(Notification, notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': 'Notification deleted successfully'}), 200

@routes.route('/send-direct-notification', methods=['POST'])
def send_direct_notification():
    """
    Endpoint to send notifications directly without using RabbitMQ.
    Useful for testing in-app notifications when RabbitMQ is not available.
    """
    data = request.json
    if not data or not all(key in data for key in ['user_id', 'type', 'title', 'content']):
        return jsonify({'error': 'Missing required fields'}), 400

    user = db.session.get(User, data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    notification_type = data['type'].lower()
    if notification_type not in ['email', 'sms', 'in-app']:
        return jsonify({'error': 'Invalid notification type'}), 400

    # Create the notification in the database
    notification = Notification(
        user_id=user.id,
        type=notification_type,
        title=data['title'],
        content=data['content']
    )
    db.session.add(notification)
    db.session.commit()

    # Handle different notification types directly
    success = False
    message = "Unknown error"

    if notification_type == 'email':
        success, message = NotificationService.send_email(
            user.email,
            data['title'],
            data['content']
        )
    elif notification_type == 'sms':
        success, message = NotificationService.send_sms(
            user.phone,
            data['content']
        )
    elif notification_type == 'in-app':
        success, message = NotificationService.send_in_app_notification(
            user.id,
            data['title'],
            data['content']
        )

    # Return the result
    return jsonify({
        'id': notification.id,
        'user_id': notification.user_id,
        'type': notification.type,
        'title': notification.title,
        'content': notification.content,
        'timestamp': notification.timestamp,
        'success': success,
        'message': message
    }), 201 if success else 500