from django import forms

from project.newsletter.models import Category, Post, Subscription


class SubscriptionForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), to_field_name="slug"
    )

    class Meta:
        model = Subscription
        fields = ["categories"]


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "categories",
            "content",
            "summary",
            "is_public",
            "is_published",
            "publish_at",
            "open_graph_description",
            "open_graph_image",
        ]
