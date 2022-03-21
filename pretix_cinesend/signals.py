import copy

from django.db import transaction
from django.db.models import Q
from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

from pretix.base.models import Order
from pretix.base.signals import (
    event_copy_data,
    item_copy_data,
    logentry_display,
    order_paid,
)
from pretix.control.signals import item_forms, nav_event_settings, subevent_forms
from pretix.presale.signals import order_info_top, position_info_top
from .forms import ItemProductForm, SubEventProductForm
from .models import ItemProduct, SubEventProduct
from .tasks import sync_order


@receiver(nav_event_settings, dispatch_uid="cinesend_nav")
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(
            request.organizer, request.event, "can_change_event_settings", request=request
    ):
        return []
    return [
        {
            "label": _("CineSend"),
            "url": reverse(
                "plugins:pretix_cinesend:settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_cinesend",
        }
    ]


@receiver(item_forms, dispatch_uid="cinesend_item_forms")
def control_item_forms(sender, request, item, **kwargs):
    try:
        inst = ItemProduct.objects.get(item=item)
    except ItemProduct.DoesNotExist:
        inst = ItemProduct(item=item)
    return ItemProductForm(
        instance=inst,
        event=sender,
        data=(request.POST if request.method == "POST" else None),
        prefix="cinesendproduct",
    )


@receiver(item_copy_data, dispatch_uid="cinesend_item_copy")
def copy_item(sender, source, target, **kwargs):
    try:
        inst = ItemProduct.objects.get(item=source)
        inst = copy.copy(inst)
        inst.pk = None
        inst.item = target
        inst.save()
    except ItemProduct.DoesNotExist:
        pass


@receiver(signal=event_copy_data, dispatch_uid="cinesend_copy_data")
def event_copy_data_receiver(sender, other, question_map, item_map, **kwargs):
    for ip in ItemProduct.objects.filter(item__event=other):
        ip = copy.copy(ip)
        ip.pk = None
        ip.event = sender
        ip.item = item_map[ip.item_id]
        ip.save()


@receiver(signal=order_paid, dispatch_uid="cinesend_paid")
def recv_order_paid(sender, order, **kwargs):
    transaction.on_commit(lambda: sync_order.apply_async(args=(sender.id, order.id)))


@receiver(signal=logentry_display, dispatch_uid="cinesend_logentry_display")
def pretixcontrol_logentry_display(sender, logentry, **kwargs):
    if logentry.action_type == "pretix_cinesend.voucher.created":
        return _("A CineSend voucher was created.")
    if logentry.action_type == "pretix_cinesend.pass.created":
        return _("A CineSend pass was created.")
    if logentry.action_type == "pretix_cinesend.fail":
        return _("A CineSend operation failed.")


def get_cinesend_status(event, qs):
    lines = []
    qs = qs.select_related(
        "item", "item__cinesend_product", "variation", "subevent__cinesend_product"
    ).prefetch_related("cinesend_vouchers", "cinesend_passes")
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
                vouchers = [v for v in pos.cinesend_vouchers.all() if v.active]
                lines.append(
                    {
                        "position": pos,
                        "type": "voucher",
                        "vouchers": vouchers,
                    }
                )
            if pos.item.cinesend_product.subscribertype_id:
                passes = [v for v in pos.cinesend_passes.all() if v.active]
                lines.append(
                    {
                        "position": pos,
                        "type": "pass",
                        "passes": passes,
                    }
                )
        except ItemProduct.DoesNotExist:
            pass
    return lines


@receiver(signal=order_info_top, dispatch_uid="cinesend_order_info_top")
def presale_o_i(sender, request, order, **kwargs):
    if order.status != Order.STATUS_PAID:
        return ""
    status = get_cinesend_status(sender, order.positions.all())
    if status:
        template = get_template("pretix_cinesend/order_info.html")
        ctx = {
            "order": order,
            "event": sender,
            "lines": status,
        }
        return template.render(ctx, request=request)
    return ""


@receiver(signal=position_info_top, dispatch_uid="cinesend_pos_info_top")
def presale_op_i(sender, request, order, position, **kwargs):
    if order.status != Order.STATUS_PAID:
        return ""
    status = get_cinesend_status(
        sender,
        order.positions.filter(Q(pk=position.pk) | Q(addon_to_id=position.pk))
    )
    if status:
        template = get_template("pretix_cinesend/order_info.html")
        ctx = {
            "order": order,
            "event": sender,
            "lines": status,
        }
        return template.render(ctx, request=request)
    return ""


@receiver(subevent_forms, dispatch_uid="cinesend_subevent_form")
def subevent_form(sender, request, subevent, copy_from, **kwargs):
    initial = None
    if copy_from:
        try:
            initial = {'asset_id': copy_from.cinesend_product.asset_id}
        except:
            pass

    try:
        inst = SubEventProduct.objects.get(subevent=subevent)
    except SubEventProduct.DoesNotExist:
        inst = SubEventProduct(subevent=subevent)
    return [
        SubEventProductForm(
            instance=inst,
            event=sender,
            data=(request.POST if request.method == "POST" else None),
            initial=initial,
            prefix="cinesendproduct",
        )
    ]
