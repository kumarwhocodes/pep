import os
import smtplib
from email.message import EmailMessage
from twilio.rest import Client
from datetime import datetime

class NotificationService:
    socketio = None

    @classmethod
    def init_socketio(cls, socketio_instance):
        cls.socketio = socketio_instance
        print("SocketIO initialized in NotificationService")

    @staticmethod
    def send_email(recipient, subject, content):
        try:
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            sender_email = os.getenv('EMAIL_SENDER')
            sender_password = os.getenv('EMAIL_PASSWORD')

            msg = EmailMessage()
            msg.set_content(content)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True, "Email notification sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    @staticmethod
    def send_sms(phone_number, content):
        try:
            account_sid = os.getenv('TWILIO_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_phone = os.getenv('TWILIO_PHONE')

            if not all([account_sid, auth_token, twilio_phone]):
                return False, "Missing Twilio credentials"

            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=content,
                from_=twilio_phone,
                to=phone_number
            )

            return True, f"SMS sent successfully. SID: {message.sid}"
        except Exception as e:
            return False, f"Failed to send SMS: {str(e)}"

    @classmethod
    def send_in_app_notification(cls, user_id, title, content):
        if cls.socketio is None:
            return False, "SocketIO not initialized"
        
        try:
            # Convert user_id to string since room names are strings
            room = str(user_id)
            
            # Create notification payload
            notification_data = {
                'user_id': user_id,
                'title': title,
                'content': content,
                'timestamp': str(datetime.utcnow())
            }
            
            # Emit to the user's room
            cls.socketio.emit('notification', notification_data, room=room)
            
            print(f"In-app notification emitted to room {room}: {title}")
            return True, "In-app notification sent"
            
        except Exception as e:
            print(f"Error sending in-app notification: {str(e)}")
            return False, f"Failed to send in-app notification: {str(e)}"