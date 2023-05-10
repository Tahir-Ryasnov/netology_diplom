import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTING_MODULE", 'order.settings')

app = Celery('order')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
