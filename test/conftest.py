import os
import uuid

from mincepy.testing import historian, mongodb_archive  # pylint: disable=unused-import
import mincepy
import pytest

import minkipy

# Display this as this is the way fixtures work! pylint: disable=redefined-outer-name


@pytest.fixture
def queue_name():
    queue_name = "test-queue:{}".format(uuid.uuid4())
    yield queue_name


@pytest.fixture
def test_queue(queue_name):
    queue = minkipy.queue(queue_name)
    yield queue
    queue.purge()


@pytest.fixture(autouse=True)
def test_project(mongodb_archive, queue_name, tmp_path):  # pylint: disable=unused-argument
    os.environ[minkipy.ENV_MINKIPY_SETTINGS] = str(tmp_path / 'settings.json')

    project = minkipy.project('minki-tests')
    project.default_queue = "default-{}".format(queue_name)

    project.kiwipy['connection_params'] = dict(uri='amqp://guest:guest@127.0.0.1',
                                               message_exchange='minki-tests',
                                               task_exchange='minki-tests',
                                               task_queue='minki-tests-queue',
                                               testing_mode=True)
    project.workon()

    yield project
    mincepy.get_historian()
