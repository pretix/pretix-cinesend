from django import forms

from .models import ItemProduct


class ItemProductForm(forms.ModelForm):
    class Meta:
        model = ItemProduct
        fields = ["asset_id", "subscribertype_id"]
        exclude = []

    def __init__(self, *args, **kwargs):
        kwargs.pop("event")
        super().__init__(*args, **kwargs)
        self.fields["asset_id"].required = False
        self.fields["asset_id"].widget.is_required = False
        self.fields["subscribertype_id"].required = False
        self.fields["subscribertype_id"].widget.is_required = False

    def save(self, commit=True):
        if (
            self.cleaned_data["asset_id"] is None
            and not self.cleaned_data["subscribertype_id"] is None
        ):
            if self.instance.pk:
                self.instance.delete()
            else:
                return
        else:
            return super().save(commit=commit)
