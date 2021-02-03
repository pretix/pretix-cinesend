from pretix.base.services.tasks import EventTask
from pretix.celery_app import app


@app.task(base=EventTask, bind=True, max_retries=10, default_retry_delay=20)
def sync_order(self, event, order_id):
    pass
