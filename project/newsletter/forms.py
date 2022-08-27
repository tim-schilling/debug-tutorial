from django import forms

from project.newsletter.models import Category, Subscription


class SubscriptionForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), to_field_name="slug"
    )

    class Meta:
        model = Subscription
        fields = ["categories"]
