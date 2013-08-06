from flask import Flask
from flask.ext.pymongo import PyMongo, AttrDict, Pagination, _underscorify
from werkzeug.exceptions import NotFound

def create_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

def initialize_item_model(db):

    class ItemQuery(db.Query):

        def special(self):
          return self.find(dict(count=4))

    class Item(db.Model):

        query_class = ItemQuery
        index = [db.Index("title", unique=True),
                 db.Index([("count", db.DESCENDING)])]

        def increment(self):
            self.query.update({'$inc': {'count': 1}})

    return Item

def initialize_entity_model(db):

    class Entity(db.Model):
        database = "testdb2"
        collection = "things"
        index = db.Index("title", unique=True)

    return Entity

def test_underscorify():
    assert _underscorify("first_second") == "first_seconds"
    assert _underscorify("FirstSecond") == "first_seconds"
    assert _underscorify("FirstSecondThird") == "first_second_thirds"
    assert _underscorify("first1_second2_third") == "first1_second2_thirds"
    assert _underscorify("firstSecond") == "first_seconds"
    assert _underscorify("FIRSTSecond") == "first_seconds"
    assert _underscorify("FIRSTSecondTHIRD") == "first_second_thirds"

def test_pagination():
    rv = Pagination(None, 1, 20, 500, [])
    assert rv.page == 1
    assert not rv.has_prev
    assert rv.has_next
    assert rv.total == 500
    assert rv.pages == 25
    assert rv.next_num == 2

class TestPyMongo(object):

    def teardown(self):
        self.db.connection.drop_database("testdb")

    def test_app_immediately_bound(self):
        app = create_app()
        self.db = PyMongo(app, database="testdb")
        assert repr(self.db) == "<PyMongo connection=mongodb://localhost:27017>"

    def test_app_delayed_bound(self):
        app = create_app()
        self.db = PyMongo(database="testdb")
        assert repr(self.db) == "<PyMongo connection=None>"
        self.db.init_app(app)
        assert repr(self.db) == "<PyMongo connection=mongodb://localhost:27017>"

    def test_ensured_indices(self):
        app = create_app()
        self.db = PyMongo(database="testdb")
        Item = initialize_item_model(self.db)
        Entity = initialize_entity_model(self.db)
        self.db.init_app(app)
        assert 'title_1' in Item.query.index_information()
        assert 'count_-1' in Item.query.index_information()
        assert 'title_1' in Entity.query.index_information()

class BaseCase(object):

    def setup(self):
        self.app = create_app()
        self.db = PyMongo(self.app, database="testdb1")
        self.Item = initialize_item_model(self.db)
        self.Entity = initialize_entity_model(self.db)

    def teardown(self):
        self.db.connection.drop_database("testdb1")
        self.db.connection.drop_database("testdb2")

class TestModel(BaseCase):

    def test_database_unspecified(self):
        assert self.Item.query.database.name == "testdb1"

    def test_database_specified(self):
        assert self.Entity.query.database.name == "testdb2"

    def test_collection_unspecified(self):
        assert self.Item.query.name == "items"

    def test_collection_specified(self):
        assert self.Entity.query.name == "things"

    def test_id_unsaved(self):
        item = self.Item(title="test")
        assert item.id is None

    def test_id_saved(self):
        item = self.Item(title="test")
        item_id = item.save()
        assert item.id == str(item_id)

    def test_remove(self):
        item = self.Item(title="test")
        item_id = item.save()
        item.remove()
        assert self.Item.query.find_one(item_id) is None

    def test_save(self):
        item = self.Item(title="test")
        item_id = item.save()
        assert self.Item.query.find_one(item_id) is not None

    def test_repr(self):
        item = self.Item(title="test", count=4)
        assert repr(item) == "Item(count=4, title='test')"

class TestQuery(BaseCase):

    def test_query(self):
        assert list(self.Entity.query.find()) == []

    def test_query_class(self):
        assert list(self.Item.query.special()) == []

    def test_find(self):
        self.Item.query.insert([
            self.Item(title="first", count=4),
            self.Item(title="second", count=7)
        ])
        assert isinstance(self.Item.query.find()[0], self.Item)

    def test_find_one(self):
        item = self.Item(title="first", count=4)
        item_id = item.save()
        assert isinstance(self.Item.query.find_one(item_id), self.Item)

    def test_find_one_str(self):
        item = self.Item(title="first", count=4)
        item_id = item.save()
        item_id = str(item_id)
        assert isinstance(self.Item.query.find_one(item_id), self.Item)

    def test_find_one_or_404(self):
        try:
            self.Item.query.find_one_or_404("1")
        except NotFound:
            assert True
        else:
            assert False

class TestCursor(BaseCase):

    def test_filter(self):
        self.Item.query.insert([
            self.Item(title="first", count=4),
            self.Item(title="second", count=7)
        ])
        assert self.Item.query.find().filter(count=4).count() == 1

    def test_paginate(self):
        self.Item.query.insert([
            self.Item(title="first", count=4),
            self.Item(title="second", count=7)
        ])
        rv = self.Item.query.find().paginate(1, per_page=1)
        assert rv.page == 1
        assert not rv.has_prev
        assert rv.has_next
        assert rv.total == 2
        assert rv.pages == 2
        assert rv.next_num == 2
        rv = rv.next()
        assert rv.has_prev
        assert not rv.has_next

class TestAttrDict(object):

    def test_init(self):
        items = AttrDict()
        assert items.keys() == []

    def test_init_iterable(self):
        items = AttrDict([('a', 4), ('b', 7)])
        assert 'a' in items

    def test_init_kwargs(self):
        items = AttrDict(a=4, b=7)
        assert 'a' in items

    def test_setitem_getitem(self):
        items = AttrDict()
        items['a'] = 4
        assert items['a'] == 4

    def test_setitem_getitem_nested(self):
        items = AttrDict()
        items['a'] = dict(b=4, c=7)
        assert items['a']['b'] == 4

    def test_setattr_getattr(self):
        items = AttrDict()
        items.a = 4
        assert items.a == 4

    def test_setattr_getattr_nested(self):
        items = AttrDict()
        items.a = dict(b=4, c=7)
        assert items.a.b == 4

    def test_delitem(self):
        items = AttrDict()
        items['a'] = 4
        del items['a']
        assert 'a' not in items

    def test_delitem_nested(self):
        items = AttrDict()
        items['a'] = dict(b=4, c=7)
        del items['a']['c']
        assert 'b' in items['a']
        assert 'c' not in items['a']

    def test_delattr(self):
        items = AttrDict()
        items.a = 4
        del items.a
        assert 'a' not in items

    def test_delattr_nested(self):
        items = AttrDict()
        items.a = dict(b=4, c=7)
        del items.a.c
        assert 'b' in items.a
        assert 'c' not in items.a

    def test_repr(self):
        items = AttrDict(a=4, b=7)
        assert repr(items) == "AttrDict([('a', 4), ('b', 7)])"
