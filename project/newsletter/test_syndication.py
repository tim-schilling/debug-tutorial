from project.newsletter.syndication import RecentCategorizedPostsFeed, RecentPostsFeed
from project.newsletter.test import DataTestCase


class TestRecentPostsFeed(DataTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.feed = RecentPostsFeed()

    def test_items(self):
        self.assertEqual(self.feed.items().first(), self.data.career_post)

    def test_item_title(self):
        self.assertEqual(
            self.feed.item_title(self.data.career_post), self.data.career_post.title
        )

    def test_item_description(self):
        self.assertEqual(self.feed.item_description(self.data.career_post), "")

    def test_item_pubdate(self):
        self.assertEqual(
            self.feed.item_pubdate(self.data.career_post), self.data.career_post.created
        )

    def test_item_categories(self):
        self.assertEqual(
            self.feed.item_categories(self.data.all_post),
            [self.data.career.title, self.data.social.title],
        )


class TestRecentCategorizedPostsFeed(DataTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.feed = RecentCategorizedPostsFeed()

    def test_get_object(self):
        self.assertEqual(
            self.feed.get_object(self.rf.get("/"), self.data.career.slug),
            self.data.career,
        )

    def test_item_title(self):
        self.assertEqual(
            self.feed.item_title(self.data.career), "Career newsletter posts"
        )

    def test_item_link(self):
        self.assertEqual(self.feed.item_link(self.data.career), "/p/?category=career")

    def test_items(self):
        self.assertEqual(
            self.feed.items(self.data.career).first(), self.data.career_post
        )
