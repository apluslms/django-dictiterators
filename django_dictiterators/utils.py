from functools import partial


class BufferEmpty:
    pass


class NestedDictIterator:
    """
    Usage in get_context_data():

    context['objects'] = NestedDictIterator.from_iterable(
        context['objects'],
        (
            ('foobar', lambda object, iterable: {
                'foobar': object.foobar,
                'something': "%s/%s" %(object.name, object.foobar),
                'objects': iterable,
            }),
            ('barbaz', lambda objecct, iterable: {
                'barbaz': object.barbaz,
                'objects': iterable,
            }),
        ),
        lambda object: {
            'object': object,
            'url': "http://myservice.com/path/%s" % (object.url),
        }
    )

    this will construct something like this (with iterators in place of [ ])

    context['objects'] = [
        {
            'foobar': "foobar",
            'something': "name/foobar",
            'objects': [
                {
                    'barbaz': "barbaz",
                    'objects': [
                        {
                            'object': object,
                            'url': "http://myservice.com/path/url"
                        }
                    ]
                }
            ]
        }
    ]

    this can be easily combined with foreachdict in templates

    {% foreachdict in objects %}
        <h1>{{ foobar }} - {{ something }}</h1>
        {% foreachdict in objects %}
            <b>{{ barbaz }}</b>
            {% foreachdict in objects %}
                <a href="{{ url }}">{{ object.name }}</a>
            {% endforeachdict %}
        {% endforeachdict %}
    {% endforeachdict %}
    """
    def __iter__(self):
        return self

    @classmethod
    def from_iterable(cls, iterable, group_by, get_dict_func):
        iterator = iter(iterable)
        root = cls.RootIterator(iterator, group_by, get_dict_func)
        return root


class ParentIterator(NestedDictIterator):
    def __init__(self, group_by, get_dict_func):
        (self.field, self.func) = group_by[0]
        group_by = group_by[1:]
        if group_by:
            self.child_class = partial(self.MidIterator,
                                       root=self.root,
                                       parent=self,
                                       group_by=group_by,
                                       get_dict_func=get_dict_func)
        else:
            self.child_class = partial(self.LeafIterator,
                                       root=self.root,
                                       parent=self,
                                       get_dict_func=get_dict_func)
        self.child = None

    def __repr__(self):
        return "<%s 0x%s on field %s>" % (self.__class__.__name__, id(self), self.field)

    def get_list(self, flatten_last=False):
        data = []
        for row in self:
            expanded = {}
            for key, value in row.items():
                if isinstance(value, NestedDictIterator):
                    expanded[key] = value.get_list(flatten_last=flatten_last)
            row.update(expanded)
            if flatten_last:
                for sublist in expanded.values():
                    row.update(sublist[-1])
            data.append(row)
        return data


class RootIterator(ParentIterator):
    def __init__(self, iterator, group_by, get_dict_func):
        self.__object = BufferEmpty
        self.__iterator = iterator
        self.stopped = False
        self.root = self

        assert bool(group_by), "NestedDictIterator doesn't serve purpose without group_by"
        super().__init__(group_by, get_dict_func)

    @property
    def object(self):
        if self.__object is BufferEmpty:
            self.__object = next(self.__iterator)
        return self.__object

    @object.deleter
    def object(self):
        self.__object = BufferEmpty

    def _get_next(self):
        try:
            obj = self.object
        except StopIteration:
            self.stopped = True
            raise

        # test if next level is completed
        if self.value != getattr(obj, self.field):
            raise StopIteration()

        return obj

    def __next__(self):
        if self.stopped:
            raise StopIteration()

        obj = self.object
        self.value = getattr(obj, self.field)
        self.child = child = self.child_class()
        return self.func(obj, child)


class MidIterator(ParentIterator):
    def __init__(self, root, parent, group_by, get_dict_func):
        self.root = root
        self.parent = parent
        self.stopped = False
        super().__init__(group_by, get_dict_func)

    def _get_next(self):
        try:
            obj = self.parent._get_next()
        except StopIteration:
            self.stopped = True
            raise

        # test if next level is completed
        if self.value != getattr(obj, self.field):
            raise StopIteration()

        return obj

    def __next__(self):
        if self.stopped:
            raise StopIteration()

        obj = self.root.object
        self.value = getattr(obj, self.field)
        self.child = child = self.child_class()
        return self.func(obj, child)


class LeafIterator(NestedDictIterator):
    def __init__(self, root, parent, get_dict_func):
        self.root = root
        self.parent = parent
        self.func = get_dict_func

    def __repr__(self):
        return "<%s 0x%s as leaf>" % (self.__class__.__name__, id(self))

    def __next__(self):
        # retrieve next object
        obj = self.parent._get_next() # can raise StopIteration
        del self.root.object # consume
        return self.func(obj)

    def get_list(self, flatten_last=False):
        return list(self)


NestedDictIterator.RootIterator = RootIterator
NestedDictIterator.MidIterator = MidIterator
NestedDictIterator.LeafIterator = LeafIterator
