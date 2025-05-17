import pika
import json
import os
from dotenv import load_dotenv

from notification_service import NotificationService
from socketio_instance import socketio 

load_dotenv("myenv.env")

NotificationService.init_socketio(socketio)

def callback(ch, method, properties, body):
    data = json.loads(body)
    success = False
    message = ""

    if data['type'] == 'email':
        success, message = NotificationService.send_email(data['email'], data['title'], data['content'])

    elif data['type'] == 'sms':
        success, message = NotificationService.send_sms(data['phone'], data['content'])

    elif data['type'] == 'in-app':
        success, message = NotificationService.send_in_app_notification(
            data['user_id'],
            data['title'],
            data['content']
        )

    print(f"[x] Notification Processed: {data['type']} -> {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost")))
    channel = connection.channel()
    channel.queue_declare(queue=os.getenv("RABBITMQ_QUEUE", "notification_queue"), durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=os.getenv("RABBITMQ_QUEUE", "notification_queue"), on_message_callback=callback)
    print("[*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    consume()