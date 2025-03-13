import json

import pika
from pika.exceptions import AMQPConnectionError

from src.settings import settings


class RabbitMQPublisher:
    def __init__(self) -> None:
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self) -> None:
        """Establish connection to RabbitMQ server"""
        try:
            credentials = pika.PlainCredentials(
                username=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASSWORD,
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare the queue
            self.channel.queue_declare(
                queue="reset-password-stream", durable=True
            )
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}")
            raise

    def publish_message(self, queue_name: str, message: dict) -> None:
        """Publish message to specified queue"""
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )
        except pika.exceptions.AMQPConnectionError:
            # Try to reconnect and publish again
            self.connect()
            self.publish_message(queue_name, message)
        except Exception as e:
            print(f"Error publishing message: {e}")
            raise

    def close(self) -> None:
        """Close the connection to RabbitMQ"""
        if self.connection and self.connection.is_open:
            self.connection.close()


# Create a singleton instance
rabbitmq_publisher = RabbitMQPublisher()


async def get_rabbitmq_publisher() -> RabbitMQPublisher:
    return rabbitmq_publisher
