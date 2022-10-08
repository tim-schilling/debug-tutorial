
# Lab 2

Let's kick it up a notch with some [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar/)!

## Lab 2.1

Change to the correct branch:

```shell
git checkout lab-2.1
```

### Report

The site seems to be running slower lately. Please make the site fast again!

To reproduce:
1. Browse to the [posts page](http://127.0.0.1:8000/p/).
1. Browse to a [post's page](http://127.0.0.1:8000/p/skill-fight-girl-north-production-thus-a-58113/).
1. Browse to the [posts admin page](http://127.0.0.1:8000/admin/newsletter/post/).
1. Why are these slow?

Note, given that we're dealing with SQLite locally, the "slowness" is largely
imaginary so please play along. Additionally the Post detail view has caching.
The cache can be cleared by opening a Django shell (``python -m manage shell``)
and running:

```python
from django.core.cache import cache
cache.clear()
```

### Facts

Let's consider what we know:

- The pages are rendering correctly and there are no errors.
- The pages were rendering "fast" earlier, but over time as the data set has grown
  they have slowed down.


### Investigation

- What queries are running?
  - Use the Django Debug Toolbar's SQL Panel
  - In a properly working case, the count should be relatively low, we're only rendering
    one type of data on the page. How many do we see?
- Should a query be using an index?
  - Fields that are likely to qualify for indexes are those that are used in
    filtering and ordering.
  - Use the SQL Panel's "Explain" button to view the database's breakdown
    of the query. Look for portions that use ``SCAN`` without mention of an
    index. This means they are iterating over the entire table comparing all
    the values.


### Conclusion

Admittedly, this is a hard area to know the "fix" for. Performance optimization
is a never ending, relentless battle.

#### Post listing admin
The admin page suffers from a [N+1 problem](https://ddg.gg?q=N%2B1+django) and
needs to make use of [``prefetch_related``](https://docs.djangoproject.com/en/4.1/ref/models/querysets/#django.db.models.query.QuerySet.prefetch_related)
since it renders each category of the post on the page. This can be chained on
the QuerySet by overriding ``ModelAdmin.get_queryset``. The need for
``prefetch_related`` is evident from the 100 duplicated queries that are fetching data from the table
``newsletter_post_categories``. That table is the intermediate table used with
a ``models.ManyToManyField``. There is a slight wrinkle in that the categories
are being rendered in order of the categories' titles. In order to push that
to the database, you must use a [``Prefetch``](https://docs.djangoproject.com/en/4.1/ref/models/querysets/#django.db.models.Prefetch)
 object that specifies:

```python
def get_queryset(self, request):
    return super().get_queryset(request).prefetch_related(
        Prefetch(
            'categories',
            queryset=Category.objects.all().order_by('title')
        )
    )
```

This means ``PostAdmin.categories_list`` would change to:

```python
@admin.decorators.display(description="Categories")
def categories_list(self, obj):
    return ", ".join(category.title for category in obj.categories.all())
```


There should also be an indexes on
``created``. Arguments could be made to add indexes on the fields that are
search-able and ``is_published``. I would stop at ``created`` because that's used
on the default loading. Any other cases would need to be proven as common
occurrences.

#### Post listing

The listing of posts also suffers from an N+1 problem, though it could use
the more simple approach of ``prefetch_related("categories")``. This is because
the template ``posts/includes/list_item.html`` doesn't order the categories
in ``{% for category in post.categories.all %}``.

There are two facets to this view that could benefit from an index. The ordering
based on ``Coalesce('publish_at', 'created')`` and the filter on ``is_published=True``.
This scenario could benefit from a multi-column index. The typical maxim is
to apply that index on the most generic columns first, to the more specific. In
this case, it would first be ``is_published``, then the coalesced datetime fields:

This would look like:

```python

class Post(TimestampedModel):
    # ...
    class Meta:
        # ...
        indexes = [
            models.Index(
                F("is_published"), Coalesce("publish_at", "created").desc(),
                name='published_posts_idx'
            )
        ]
```

Interestingly enough (I'm not a DBA), the above only covers the count
portion of the view. The pagination that selects the data does not hit
this index and requires a different index.

```python

class Post(TimestampedModel):
    # ...
    class Meta:
        # ...
        indexes = [
            models.Index(
                Coalesce("publish_at", "created").desc(),
                name='recent_first_idx'
            )
        ]
```

As a peer, I would probably resort to only using ``recent_first_idx`` and
waiting until the site slowed down and required a more finely tuned index.
However, there is the argument to be made that both are necessary.

#### Post detail

This view generates a fixed number of queries, but does a scan on the
entire table for the slug field, ``SCAN TABLE newsletter_post``. The solution
here is to either use ``CharField(..., db_index=True)`` or switch to
``SlugField(...)`` which automatically creates an index under the hood.


### Further consideration

Please keep in mind to avoid pre-optimizations. This exercise exists to help
you go to the furthest extent possible in those cases where we need to
squeeze all the speedy goodness out of the application.

That said, consider the application(s) you work on. What are the most
frequently used parts? What do you have in place to catch slowness?
Could you benefit from using [``assertNumQueries(...)``](https://docs.djangoproject.com/en/4.1/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries)?


## Lab 2.2

Change to the correct branch:

```shell
git checkout lab-2.2
```

### Report

The analytics view specifically is running slow. Can you take a look at it?

To reproduce:
1. Browse to the [analytics page](http://127.0.0.1:8000/analytics/).
1. Why has this become slow?

Note, if you're running a nice machine, this slowness may be imaginary. So please
humor me and pretend it's slow.

### Facts

Let's consider what we know:

- The page was rendering correctly and there are no errors.
- The page was rendering "fast" when it was first introduced, but has since slowed
  down.


### Investigation

- Do we have a fixed number of queries running?
- Are the queries running in a reasonable amount of time?
- Is there a section of code that's running slowly?
  - Enable the Profiling panel and refresh the page.
  - If the slowness isn't obviously from the SQL panel, we need to see where time
    is being spent in the application.
  - Look for long durations or a high number of iterations.
  - Can the code be refactored to run more efficiently?

### Conclusion

The solution here is to rework the entire Analytics view to push the calculations
into the database. The view is doing simple filter and aggregate work so it makes
little sense to pull the entire model instance out of the database for each row.
Additionally, it's creating a new datetime instance in ``determine_buckets`` and
performing three logical comparisons for every ``Post`` and ``Subscription``. Not
to mention ``analyze_categorized_model`` does another three logical comparisons
for each instance.

The Profiling panel highlights the lines of code that exist in our project to
help draw our eyes to where the problem is most likely caused.

### Further consideration

Similar to the previous lab, knowing when to use a profiler can be difficult.
Rather than applying it everywhere, it makes the most sense to start with either
knowingly slow areas or critical areas. Take a moment to reflect on your own
coding journey and any times that a profiler would have been helpful.


## Lab 2.3

Change to the correct branch:

```shell
git checkout lab-2.3
```

### Report

I think the analytics view is broken. The values don't match what I'd expect
to see, can you look into them?

To reproduce:
1. Browse to the [analytics page](http://127.0.0.1:8000/analytics/).
1. It doesn't work.

### Facts

Let's consider what we know:

- The page is rendering correctly but the data may be wrong.
- It's unknown if this was ever working correctly, but it certainly is wrong now.


### Investigation

- What values should we expect to see on the analytics page?
  - For this you need to inspect the database somehow, here are a few options.
  - Open up a repl with ``python -m manage shell`` and query the data.
    - ```python
      from datetime import timedelta
      from django.utils import timezone
      from project.newsletter.models import Post, Subscription
      print(
          "Posts",
          Post.objects.filter(
              created__gte=timezone.now() - timedelta(days=180)
          ).count()
      )
      print(
          "Subscriptions",
          Subscription.objects.filter(
              created__gte=timezone.now() - timedelta(days=180)
          ).count()
      )
      ```
  - Use the SQLite browser by opening the file directly (you must have SQLite already installed).
    ```sqlite
    SELECT COUNT(*) FROM newsletter_post WHERE created >= date('now','-180 day');
    SELECT COUNT(*) FROM newsletter_subscription WHERE created >= date('now','-180 day');
    ```
  - Open a SQLite shell with ``python -m manage dbshell``  (you must have SQLite already installed).
    ```sqlite
    SELECT COUNT(*) FROM newsletter_post WHERE created >= date('now','-180 day');
    SELECT COUNT(*) FROM newsletter_subscription WHERE created >= date('now','-180 day');
    ```
- What is different in the query that causes the Post count to return correctly,
  but not the Subscription count?
  - Use the SQL Panel to inspect the query that is counting the objects.
  - Click on the "+" button on the left to expand the query.
  - It may be easier to read clicking on the "Select" button.
  - You can also improve the readability by copying and pasting the query into
    an online formatter such as [sqlformat.org](https://sqlformat.org)
- Does removing ``categories__isnull=False`` from the ``Subscription`` QuerySet
  resolve the issue?
- Does adding ``categories__isnull=False`` to the ``Post`` QuerySet cause
  an unexpected result?
- Why does the inclusion of the join, ``LEFT OUTER JOIN "newsletter_subscription_categories"``
  cause duplicates?
  - This is because the joined table may have multiple matches for any Subscription
    row causing the ``Count`` function to find more than one, leading to an inflated
    count.
  - This can be fixed by using an appropriate ``GROUP BY`` clause in the SQL.
  - What does the Django ORM's ``Count`` expression offer in terms of parameters?
    - You can use the [docs](https://docs.djangoproject.com/en/4.1/ref/models/querysets/#id9)
      or inspect [the code](https://github.com/django/django/blob/stable/4.1.x/django/db/models/aggregates.py#L145-L149)
      (right click on ``Count`` and choose "Go To Definition") in
      your IDE if you're using PyCharm or VSCode.
    - We can see that ``Count`` subclasses [``Aggregate`` which has ``distinct`` as
      a param](https://github.com/django/django/blob/e151df24ae2b0a388fc334a6f1dcb31110d5819a/django/db/models/aggregates.py#L25-L35).

### Conclusion

The solution here is to use ``distinct=True`` in the call to ``Count``. Traversing
many to many relationships or reverse foreign key relationships can be tricky. You
don't want to use ``distinct()`` and ``distinct=True`` everywhere because if it's
unnecessary, you're needlessly slowing down your application.

This problem highlights one of the underlying issues with using an ORM. It
abstracts away the underlying SQL and makes it easy to misunderstand what the
database is doing.

### Further consideration

This bug is very insidious, it's easy to miss in development and a code review.
It's possible to write a test that misses it if the data is setup such
that there is only one category for each subscription. Finally, a developer may
not be familiar with the data to know when a value "looks wrong" resulting in
the bug being found downstream by the actual users. Can you think of some practices
that would help avoid this bug?


## Lab 2.4

Change to the correct branch:

```shell
git checkout lab-2.4
```

### Report

Thank you for adding caching to the site recently, but I think you broke something.
A post that shouldn't be public is available to the public now.

To reproduce:
1. Log into your staff account and browse to the [published posts](http://127.0.0.1:8000/p/skill-fight-girl-north-production-thus-a-58113/).
1. Use an incognito window to also view the [published posts](http://127.0.0.1:8000/p/skill-fight-girl-north-production-thus-a-58113/).
1. In the incognito window, click to read a post.
1. In the staff authenticated window, click "Set to private" for the post opened
   in the incognito window.
1. In the incognito window, refresh the page.
1. This should 404, but it's still available to the public.


### Facts

Let's consider what we know:

- The page was properly requiring authenticated users for private
  posts before caching was added.
- We only set the cached response for ``view_post`` when a ``Post``
  is public.
- We are clearing the cache for a ``Post`` when it's updated via a
  signal handler in ``receivers.py``.

### Investigation

- Why does the post still return despite being private?
  - Use the Django Debug Toolbar's Cache Panel to inspect what cache
    operations are occurring.
- Does the page return a 404 when the cache isn't set?
  - Open a Django shell ``python -m manage shell``:
    ```python
    from django.core.cache import cache
    cache.clear()
    ```
  - Refresh the page to see if it 404's.
- Does updating a post to be private via the update view result in the
  cache being busted?
  1. You can edit a post via the "Edit" link near the top of the detail page.
    Otherwise the URL is ``http://127.0.0.1:8000/post/<post_slug>/update/``
  1. Save the post.
     - The response is a redirect to avoid multiple posts.
     - However, this means the toolbar is presenting you the data for the 301
       redirect response, not your POST request.
  1. Click on the History Panel
  1. Find the POST request to the ``.../update/`` URL and click "Switch".
  1. Click on the Cache Panel and view the operations.
- Does "Set to private" / "Set to public" delete the cache instance?
  1. Browse to the [post listing page](http://127.0.0.1:8000/p/).
  1. Click "Set to private" or "Set to public"
  1. Click the History Panel.
  1. Find the POST to the ``.../toggle_privacy/`` URL and click "Switch".
  1. Inspect the Cache Panel for operations.
- What is different between how ``toggle_post_privacy`` and ``update_post``
  save the data changes?

### Conclusion

The root cause here is that ``Post.objects.filter(...).update()`` does not
trigger the ``post_save`` signal. This means the cache key is not deleted
leading to posts continuing to be publically available.

There are a couple of solutions. One is to clear the cache in ``toggle_post_privacy``.
Another would be to avoid using ``.update()``, but only change the public
field via:

```python
post = get_objects_or_404(...)
post.is_public != post.is_public
# Include updated to keep our updated timestamp fresh.
post.save(update_fields=['is_public', 'updated'])
```

The above will only change the fields we intended to change. It does mean
a second database query (1 to fetch, 1 to update), but that's pretty minor.

A third option is to stop using on ``post_save`` for cache invalidation
and to handle all that logic manually within functions in the
``operations.py`` module. This approach is has more philosophical
implications that you'd need to sort out. Such as, what do you do about
``ModelForm`` instances since they mutate the database?


### Further consideration

You probably already know the typical questions I am going to ask.
So I won't ask them. After using the Django Debug Toolbar throughout
this lab, what would make your life better as a developer? Could you
find some time to submit an issue and open a PR?
