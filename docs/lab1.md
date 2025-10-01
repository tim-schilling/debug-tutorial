
# Lab 1

Let's put those basics to the test.

## Lab 1.1

Change to the correct branch:

```shell
git checkout lab-1.1
```

### Report

The detail view for the post "Term writer recognize race available." is broken.

To reproduce:
1. Browse to the [posts page](http://127.0.0.1:8000/p/).
2. Click on "Read" for the post with the title "Term writer recognize race available."
3. "It doesn't work!"

### Facts

Let's consider what we know:

- The error message is ``Post matching query does not exist.``, implying the
  QuerySet does not contain a Post matching the filters.
- The line that causes the error is on line 80:``post = posts.get(title=lookup)``
- We know the post exists, we can find it in the
  [admin](http://127.0.0.1:8000/admin/newsletter/post/?q=Term+writer+recognize+race+available.)
- This impacts more than just the post in the report. The detail
  view is broken for all posts.


### Investigation

- What is being used to look up the Post instance?
- Where is that lookup value coming from?
- How does the link generate the URL to supply that lookup value?


### Conclusion

In this scenario, the Post's slug field is being used to generate the
URL, while the view expects the title to be passed in.

This is an example of a bug in which the error report provides the majority
of the information we need, but we have to read closely and correctly
interpret the information. Try to avoid making assumptions about what you
expect the error to be. Sometimes we'll see an exception type and think,
"Oh, that obviously has to be in XYZ." But upon reading the actual error
message and looking at the stacktrace, we discover it's from ABC.

To solve this, we should pass ``post.slug`` into the calls for generating
``newsletter:view_post``. I'd also argue that the URL parameter should be
renamed to ``slug`` to be more explicit about what is expected.

For example, it's easier to spot the bug in this code during a code review:

```python
post = posts.get(title=slug)
```

than

```python
post = posts.get(title=lookup)
```

### Further consideration

This view uses ``post = posts.get(...)`` to fetch a single instance. When
that doesn't exist, it's resulting in an uncaught exception which causes a 500
error. Instead we should use ``post = get_object_or_404(posts, ...)`` to get a
more friendly and less noisy 404 response. But consider what this error report
would look like if that's how the code worked; we wouldn't have an error message
or a stacktrace. We simply would see that the view is returning our HTTP 404 template
implying the Post doesn't exist when we know it does.

What I'd like you to think about for a minute is how you would approach this problem
in that scenario (the view is returning a 404 response when it shouldn't)?


## Lab 1.2

This lab covers a very common error, but hard to diagnosis when it's an
[unknown unknown](https://www.techtarget.com/whatis/definition/unknown-unknown).

Change to the correct branch:

```shell
git checkout lab-1.2
```

### Report

Creating posts is broken. The open graph image doesn't get uploaded!


To reproduce:
1. Browse to the [create post page](http://127.0.0.1:8000/post/create/).
2. Fill out the form fields with some filler information.
3. Select an image for "Open graph image"
4. Click save.
5. The update form does not contain the file for the Open graph image field.
6. "It doesn't work!"

### Facts

Let's consider what we know:

- The form is hitting the correct view and is using the form class we
  expect since the post is created with the non-file fields.


### Investigation

- Does the file show up on the server side?
  - Using the IDE's debugger, a ``breakpoint()`` line or a print statement, inspect
    [``request.FILES``](https://docs.djangoproject.com/en/stable/ref/request-response/#django.http.HttpRequest.FILES).
  - Are there any files included? Is ``"open_graph_image"`` a key?
- Is the file being sent from the browser to the server?
  - We can use the browser's Developer Tool's Network panel to inspect the request.
  - Browse to the [create view](http://127.0.0.1:8000/post/create/).
  - Open the developer tools, click on the networking panel.
  - Populate and submit the form.
  - Look for the image content in the request.
  - What value is being sent? Does it look like a file or the name of the file?
- Can we create a Post with an Open graph image [in the admin](http://127.0.0.1:8000/admin/newsletter/post/add/)?
- What is different between creating a Post in the admin versus
  creating a Post in our own application?
  - Compare the rendered ``<input>`` elements for ``open_graph_image``.
  - Compare the containing ``form`` element on the for those inputs.

### Conclusion

In this scenario the ``<form>`` element on that's used for creating/updating
a Post is missing the [proper ``enctype="multipart/form-data""`` attribute](https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/enctype).
This is 100% one of those, need to remember parts for web development.

However, by asking the above questions, we can determine that this attribute is what's
needed without knowing about it in the first place. You're never going to know
everything about everything so you will benefit from developing skills that
help you reveal those unknown unknowns.

By starting with the fact that the server is not getting a file, we know the
browser isn't doing what we expected. From there, we can compare a broken case
to a working case, the application's create view to the admin's add Post view.
Comparing those requests, we saw that the admin request was including binary data
while the application view simply sent the string of the file name.

The next step is the most difficult jump in this lab. We either need to
understand how HTML encodes forms/data or have a discerning eye to compare the
two forms and spot the differences then experiment to identify which of those
differences is the cause of the problem.

Knowing what the ``enctype`` attribute does will always be faster
than investigative trial and error, but the skills used in that investigative
trial and error can be reused on other problems.


### Further consideration

How can you prevent this type of error from occurring in your applications? What
can you do during development, testing or code reviews to catch this before it
makes it way into production?



## Lab 1.3

Change to the correct branch:

```shell
git checkout lab-1.3
```

### Report

The list of posts is broken! The datetime strings should generally be in
order of most recent to oldest, but they appear jumbled.


To reproduce:
1. Browse to the [list posts](http://127.0.0.1:8000/p/) view.
2. The dates are ordered from most recent to oldest, but posts such as
   "Campaign expect page information wrong more." and "Example
   become begin wish painting economic."
   appear out of order in comparison to "Skill fight girl north
   production thus a." and "New star by chair environmental family Congress degree."
3. "It doesn't work!"

### Facts

Let's consider what we know:

- Either the posts are being returned in a jumbled order or the datetime
  string is being rendered incorrectly.

### Investigation

- How are the posts being ordered for ``newsletter.views.list_posts``?
- What is rendering the datetime string on the page?

### Conclusion

The posts are being ordered correctly, ``publish_at`` first, falling back to
``created`` when unset. Therefore the template must be rendering incorrectly.
This can be confirmed by comparing the fields of the posts that render
[correctly](http://127.0.0.1:8000/admin/newsletter/post/?slug=hear-after-debate-thousand-medical-give-85694)
and [incorrectly](http://127.0.0.1:8000/admin/newsletter/post/?slug=add-they-debate-guess-leg-21809).
From the admin, we can see the correctly rendering Post does not have a value
for ``publish_at``, while the incorrectly rendering Post does have a value
for ``publish_at``. We can see that the ``publish_at`` value is significantly
more recent than the ``created`` value which explains why it appears in the
list of posts at the top.

We can also infer that since the ``publish_at`` is the ``order_by`` value,
that it should also be the value used when rendering the datetime string.

Now we know that the template is likely using the ``created`` field to render
the datetime string when it shouldn't be. However, the template that's used
to render the individual posts doesn't contain ``post.created`` explicitly.
But we do see that there's a custom template tag that's rendering the datetime
called ``nice_datetime``. Looking at that code, we indeed find the
``timestamp`` variable being set to the value of ``post.created`` when it
should be ``post.publish_date``.


### Further consideration

This is a straightforward example with an underlying concept. You must
be able to switch between assuming that some part of the code works and knowing
that some part of the code must contain an error. Was there a time when you
incorrectly assumed a bug could not be in a component only to find that your
assumption was wrong? Why were you so confident in that assumption? How can
you learn to hold these opinions more loosely in the future?


---

Good work!

I hope you were able to find something to take away from
this lab. Proceed to [Lab 2](lab2.md).
