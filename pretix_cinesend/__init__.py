from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.2.0"


class PluginApp(PluginConfig):
    name = "pretix_cinesend"
    verbose_name = "CineSend"

    class PretixPluginMeta:
        name = gettext_lazy("CineSend")
        author = "pretix team"
        description = gettext_lazy("Connects pretix to CineSend")
        visible = True
        version = __version__
        category = "INTEGRATION"
        compatibility = "pretix>=3.14.0"

    def ready(self):
        from . import signals, tasks  # NOQA


default_app_config = "pretix_cinesend.PluginApp"
