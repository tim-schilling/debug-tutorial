from django.contrib import admin

from project.newsletter.models import (
    Category,
    Post,
    Subscription,
    SubscriptionNotification,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "slug"]
    search_fields = ["title", "slug"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "slug",
        "is_published",
        "publish_at",
        "categories_list",
        "created",
        "updated",
    ]
    list_filter = ["is_published", "categories"]
    search_fields = ["title", "slug", "content"]
    ordering = ["-created"]
    raw_id_fields = ["author"]

    @admin.decorators.display(description="Categories")
    def categories_list(self, obj):
        return ", ".join(
            category.title for category in obj.categories.order_by("title")
        )

    def get_changeform_initial_data(self, request):
        return {"author": request.user}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user_email", "categories_list"]
    list_select_related = ["user"]
    search_fields = ["categories__title", "user__username", "user__email"]

    @admin.decorators.display(description="Categories")
    def categories_list(self, obj):
        return ", ".join(category.title for category in obj.categories.all())

    @admin.decorators.display(ordering="user__email")
    def user_email(self, obj):
        return obj.user.email


@admin.register(SubscriptionNotification)
class SubscriptionNotificationAdmin(admin.ModelAdmin):
    list_display = ["user_email", "post", "sent", "created"]
    list_select_related = ["subscription__user", "post"]

    @admin.decorators.display(ordering="subscription__user__email")
    def user_email(self, obj):
        return obj.subscription.user.email
