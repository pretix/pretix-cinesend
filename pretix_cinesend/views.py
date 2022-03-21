import logging
from django import forms
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.forms import SecretKeySettingsField, SettingsForm
from pretix.base.models import Event
from pretix.control.signals import subevent_forms
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin

logger = logging.getLogger(__name__)


class CinesendSettingsForm(SettingsForm):
    cinesend_environment = forms.ChoiceField(
        label=_("Environment"),
        choices=(
            ("api.cinesend.com", _("Production")),
            ("staging-api.cinesend.com", _("Staging")),
        ),
    )
    cinesend_api_key = SecretKeySettingsField(
        label="API Key",
        required=False,
    )
    cinesend_exclude_addons = forms.BooleanField(
        label=_('Exclude add-on products'),
        required=False,
    )
    cinesend_voucher_landingpage = forms.BooleanField(
        label=_('Use landing page URL for vouchers'),
        required=False,
    )


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = CinesendSettingsForm
    template_name = "pretix_cinesend/settings.html"
    permission = "can_change_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_cinesend:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
