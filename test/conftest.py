import pymongo
import pytest

import mincepy

import minkipy


@pytest.fixture
def mongodb_archive():
    client = pymongo.MongoClient()
    db = client['minki-tests']
    mongo_archive = mincepy.mongo.MongoArchive(db)
    yield mongo_archive
    client.drop_database(db)


@pytest.fixture
def historian(mongodb_archive):
    hist = mincepy.Historian(mongodb_archive)
    hist.register_types(mincepy.testing.HISTORIAN_TYPES)
    mincepy.set_historian(hist)
    yield hist
    mincepy.set_historian(None)


@pytest.fixture
def test_project(mongodb_archive):
    project = minkipy.project('minki-tests')
    project.kiwipy['connection_params'] = 'amqp://guest:guest@127.0.0.1'
    project.workon()

    yield project
    mincepy.get_historian()
