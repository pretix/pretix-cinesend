import logging
import requests
from pretix.base.models import Order, OrderPosition
from pretix.base.services.tasks import EventTask
from pretix.celery_app import app

from pretix_cinesend.models import ItemProduct

logger = logging.getLogger(__name__)


@app.task(base=EventTask, bind=True, max_retries=10, default_retry_delay=20)
def create_voucher(self, event, op_id):
    op = (
        OrderPosition.objects
        .select_related("order", "item", "item__cinesend_product", "subevent__cinesend_product")
        .get(pk=op_id)
    )
    if op.subevent and hasattr(op.subevent, 'cinesend_product') and op.subevent.cinesend_product.asset_id:
        asset_id = op.subevent.cinesend_product.asset_id
    else:
        asset_id = op.item.cinesend_product.asset_id

    if op.cinesend_vouchers.filter(active=True).exists():
        return

    r = requests.post(
        f"https://{event.settings.cinesend_environment}/api/integrators/vouchers",
        data={
            "apiKey": event.settings.cinesend_api_key,
            "orderID": "{}-{}".format(op.order.full_code, op.positionid),
            "contentID": asset_id,
            "landingPage": "true" if event.settings.cinesend_voucher_landingpage else "false",
        },
    )
    r.raise_for_status()
    data = r.json()
    if data["success"]:
        op.cinesend_vouchers.create(
            active=True,
            code=data["voucher_code"],
            url=data["voucher_url"],
        )
        op.order.log_action(
            "pretix_cinesend.voucher.created",
            data={"position": op.id, "positionid": op.positionid, "response": data},
        )
    else:
        op.order.log_action("pretix_cinesend.fail", data={"response": data})


@app.task(base=EventTask, bind=True, max_retries=10, default_retry_delay=20)
def create_pass(self, event, op_id):
    op = OrderPosition.objects.select_related(
        "order", "item", "item__cinesend_product"
    ).get(pk=op_id)
    subscribertype_id = op.item.cinesend_product.subscribertype_id

    if op.cinesend_passes.filter(active=True).exists():
        return

    r = requests.post(
        f"https://{event.settings.cinesend_environment}/api/integrators/subscribers",
        data={
            "apiKey": event.settings.cinesend_api_key,
            "name": op.attendee_name or "Ticket customer",
            "email": op.attendee_email or op.order.email,
            "sendEmail": "1",
            "subscriberTypeIDs": subscribertype_id,
        },
    )
    r.raise_for_status()
    data = r.json()
    if data["success"]:
        op.cinesend_passes.create(
            active=True,
            subscriber_id=data["subscriber_id"],
            invite_url=data["invite_url"],
        )
        op.order.log_action(
            "pretix_cinesend.pass.created",
            data={"position": op.id, "positionid": op.positionid, "response": data},
        )
    else:
        op.order.log_action("pretix_cinesend.fail", data={"response": data})


@app.task(base=EventTask, bind=True, max_retries=10, default_retry_delay=20)
def sync_order(self, event, order_id):
    order = Order.objects.get(pk=order_id)
    if order.status != Order.STATUS_PAID:
        return
    if not event.settings.cinesend_api_key:
        return

    qs = order.positions.select_related("item", "item__cinesend_product")
    if event.settings.cinesend_exclude_addons:
        qs = qs.filter(addon_to__isnull=True)
    for pos in qs:
        has_asset = False
        try:
            has_asset = pos.item.cinesend_product.asset_id
        except:
            pass
        try:
            has_asset = has_asset or pos.subevent.cinesend_product.asset_id
        except:
            pass
        try:
            if has_asset:
                create_voucher.apply_async(args=(event.pk, pos.pk))
            if pos.item.cinesend_product.subscribertype_id:
                create_pass.apply_async(args=(event.pk, pos.pk))
        except ItemProduct.DoesNotExist:
            pass
