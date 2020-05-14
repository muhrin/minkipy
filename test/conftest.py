import os
import uuid

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
    # Make sure the queue is empty in case it was created before
    minkipy.queue(queue_name).purge()
    yield queue
    minkipy.queue(queue_name).purge()


@pytest.fixture(autouse=True)
def test_project(queue_name, tmp_path):
    os.environ[minkipy.ENV_MINKIPY_SETTINGS] = str(tmp_path / 'settings.json')

    project = minkipy.project('minki-tests')
    project.default_queue = "default-{}".format(queue_name)

    project.kiwipy['connection_params'] = dict(uri='amqp://guest:guest@127.0.0.1',
                                               message_exchange='minki-tests',
                                               task_exchange='minki-tests',
                                               task_queue='minki-tests-queue',
                                               testing_mode=True)
    project.set_as_active()

    project.workon()
    # Make sure the queue is empty in case it was created before
    minkipy.queue(project.default_queue).purge()

    yield project

    # Cleanup
    minkipy.queue(project.default_queue).purge()
