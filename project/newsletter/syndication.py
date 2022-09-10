from django.contrib.syndication.views import Feed

from project.newsletter.models import Category, Post


class RecentPostsFeed(Feed):
    title = "Newsletter posts"
    description = "Categorized newsletter posts from Tim."

    def items(self):
        return (
            Post.objects.recent_first()
            .published()
            .public()
            .prefetch_related("categories")[:30]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return ""

    def item_pubdate(self, item):
        """
        Takes an item, as returned by items(), and returns the item's
        pubdate.
        """
        return item.publish_date

    def item_categories(self, item):
        """
        Takes an item, as returned by items(), and returns the item's
        categories.
        """
        return [category.title for category in item.categories.all()]


class RecentCategorizedPostsFeed(RecentPostsFeed):
    description = "Categorized newsletter posts from Tim."

    def get_object(self, request, slug):
        return Category.objects.get(slug=slug)

    def item_title(self, obj):
        return f"{obj.title} newsletter posts"

    def item_link(self, obj):
        return "/p/" + f"?category={obj.slug}"

    def items(self, obj):
        return (
            Post.objects.in_category(obj)
            .recent_first()
            .published()
            .public()
            .prefetch_related("categories")[:30]
        )
