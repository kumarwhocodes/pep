from flask import Flask
from dotenv import load_dotenv
from socketio_instance import socketio
from models import db
from routes import routes
from notification_service import NotificationService

load_dotenv("myenv.env")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notification.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(routes)
socketio.init_app(app, cors_allowed_origins="*")

# Inject SocketIO into NotificationService
NotificationService.init_socketio(socketio)

# Import socket event handlers
import server_socket_events

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)