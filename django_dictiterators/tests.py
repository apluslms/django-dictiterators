from django.test import TestCase

from .utils import NestedDictIterator
from pprint import PrettyPrinter
pprint = PrettyPrinter(width=10).pprint


class TestObject:
    def __init__(self, foo, bar, baz):
        self.foo = foo
        self.bar = bar
        self.baz = baz

    def __repr__(self):
        return "O(%s, %s, %s)" % (self.foo, self.bar, self.baz)


class IteratorTestCase(TestCase):
    def setUp(self):
        data = [TestObject(i, j, k) for i in range(2) for j in range(2) for k in range(3)]

        model = []
        foo_bucket = []
        bar_bucket = []
        prev = None
        for obj in data:
            if prev and (obj.foo != prev.foo or obj.bar != prev.bar):
                foo_bucket.append({'bar': prev.bar, 'sub': bar_bucket})
                bar_bucket = []
            if prev and obj.foo != prev.foo:
                model.append({'foo': prev.foo, 'sub': foo_bucket})
                foo_bucket = []
            bar_bucket.append({'baz': obj.baz})
            prev = obj
        if bar_bucket:
            foo_bucket.append({'bar': prev.bar, 'sub': bar_bucket})
        if foo_bucket:
            model.append({'foo': prev.foo, 'sub': foo_bucket})


        self.data = data
        self.model = model
        self.iterator = NestedDictIterator.from_iterable(
            data,
            (
                ('foo', lambda obj, iterable: {
                    'foo': obj.foo,
                    'sub': iterable,
                }),
                ('bar', lambda obj, iterable: {
                    'bar': obj.bar,
                    'sub': iterable,
                }),
            ),
            lambda obj: {'baz': obj.baz},
        )


    def test_basic(self):
        """Basic iterator test"""
        test_data = []
        for d in self.iterator:
            sublist = []
            for d2 in d['sub']:
                sublist2 = []
                for d3 in d2['sub']:
                    sublist2.append(d3)
                d2['sub'] = sublist2
                sublist.append(d2)
            d['sub'] = sublist
            test_data.append(d)

        self.assertEqual(test_data, self.model)

    def test_get_list(self):
        """Test method .get_list()"""
        test_data = self.iterator.get_list()

        self.assertEqual(test_data, self.model)
