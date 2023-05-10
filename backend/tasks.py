from django.dispatch import Signal, receiver

from backend.models import User
from order.celery import app
from django.conf import settings


@app.task()
def send_email(title, message, email, *args, **kwargs):
    recipient_list = [email]
    from_email = settings.DEFAULT_FROM_EMAIL
    return send_email(subject=title,
                      message=message,
                      from_email=from_email,
                      recipient_list=recipient_list,
                      fail_silently=False)


new_order = Signal(providing_args=['user_id'], )


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    subject = 'Changing the order status'
    message = 'The order has been formed'
    user = User.objects.get(id=user_id)
    email = user.email
    send_email.apply_async((subject, message, email), countdown=60)
