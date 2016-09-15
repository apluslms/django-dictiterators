Django dict iterators
=====================

Simple template related tools to handle iterators with more complex data than just model objects.

You would have something like following in your views.py

```python
context['data'] = (
    {
        'obj': obj,
        'form': Form(instance=obj),
        'post_url': reverse('post_to', kwargs={'pk': obj.pk}),
    } for obj in object_list
)
```

And then this in your template

```html+django
{% load dictiterators %}

{% foreachdict in data %}
    <h1> {{ obj.title }} </h1>

    <form action="{{ post_url }}" method="post">
        {{ form }}
    </form>
{% endforeachdict %}
```

For above to work add `django_dictiterators` in your django projects settings `INSTALLED_APPS` list.
