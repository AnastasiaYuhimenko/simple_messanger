# если я забыла че это такое, то это файлик с настройками celery

from celery import Celery

celery_app = Celery(
    "tasks", broker="redis://redis:6379/0", backend="redis://redis:6379/0"
)

import services.celery_service
