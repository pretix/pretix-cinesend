from django.utils.translation import gettext_lazy
from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_cinesend"
    verbose_name = "CineSend"

    class PretixPluginMeta:
        name = gettext_lazy("CineSend")
        author = "pretix team"
        description = gettext_lazy("Automatically grant access to your CineSend event to your customers.")
        picture = "pretix_cinesend/logo.svg"
        visible = True
        version = __version__
        category = "INTEGRATION"
        compatibility = "pretix>=3.14.0"

    def ready(self):
        from . import signals, tasks  # NOQA

