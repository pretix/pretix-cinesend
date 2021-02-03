import copy

from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _

from pretix.base.signals import item_copy_data, event_copy_data, order_paid
from pretix.control.signals import nav_event_settings, item_forms
from .forms import ItemProductForm
from .models import ItemProduct
from .tasks import sync_order


@receiver(nav_event_settings, dispatch_uid='cinesend_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(request.organizer, request.event, 'can_change_event_settings',
                                             request=request):
        return []
    return [{
        'label': _('CineSend'),
        'url': reverse('plugins:pretix_cinesend:settings', kwargs={
            'event': request.event.slug,
            'organizer': request.organizer.slug,
        }),
        'active': url.namespace == 'plugins:pretix_cinesend',
    }]


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
        prefix="cinesendproduct"
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
    for ip in ItemProduct.objects.fitler(item__event=other):
        ip = copy.copy(ip)
        ip.pk = None
        ip.event = sender
        ip.item = item_map[ip.item_id]
        ip.save()


@receiver(signal=order_paid, dispatch_uid="cinesend_paid")
def recv_order_paid(sender, order, **kwargs):
    sync_order.apply_async(args=(sender.id, order.id))
