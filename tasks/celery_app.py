import os
from celery import Celery


def make_celery(app_name="jwt_auth_app"):
    broker_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    always_eager = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "True").lower() in ("true", "1", "t")

    celery_instance = Celery(
        app_name,
        broker=broker_url,
        backend=result_backend,
    )
    celery_instance.conf.update(
        task_always_eager=always_eager,
        task_eager_propagates=True,
        result_expires=3600,
    )
    return celery_instance


celery_app = make_celery()
