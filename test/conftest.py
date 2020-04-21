import os
import uuid

from mincepy.testing import historian, mongodb_archive  # pylint: disable=unused-import
import mincepy
import pytest

import minkipy


@pytest.fixture(autouse=True)
def test_project(mongodb_archive, tmp_path):  # pylint: disable=unused-argument, redefined-outer-name
    os.environ[minkipy.ENV_MINKIPY_SETTINGS] = str(tmp_path / 'settings.json')

    project = minkipy.project('minki-tests')
    project.kiwipy['connection_params'] = 'amqp://guest:guest@127.0.0.1'
    project.workon()

    yield project
    mincepy.get_historian()


@pytest.fixture
def test_queue():
    queue_name = "test-queue:{}".format(uuid.uuid4())
    queue = minkipy.queue(queue_name)
    yield queue
    queue.purge()
