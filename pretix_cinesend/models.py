from django.db import models
from django.utils.translation import gettext_lazy as _


class SubEventProduct(models.Model):
    subevent = models.OneToOneField(
        "pretixbase.SubEvent", related_name="cinesend_product", on_delete=models.CASCADE
    )
    asset_id = models.CharField(max_length=200, verbose_name=_("CineSend Asset ID"),
                                help_text=_("Has precedence over any values set on product level"))


class ItemProduct(models.Model):
    item = models.OneToOneField(
        "pretixbase.Item", related_name="cinesend_product", on_delete=models.CASCADE
    )
    asset_id = models.CharField(max_length=200, verbose_name=_("CineSend Asset ID"))
    subscribertype_id = models.CharField(
        max_length=200, verbose_name=_("CineSend SubscriberType ID")
    )


class CineSendVoucher(models.Model):
    position = models.ForeignKey(
        "pretixbase.OrderPosition",
        related_name="cinesend_vouchers",
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=200)
    url = models.URLField(blank=True, null=True)


class CineSendPass(models.Model):
    position = models.ForeignKey(
        "pretixbase.OrderPosition",
        related_name="cinesend_passes",
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(default=True)
    subscriber_id = models.CharField(max_length=200)
    invite_url = models.URLField(blank=True, null=True)
