import os
import pytest

from mincepy.testing import historian, mongodb_archive
import mincepy

import minkipy


@pytest.fixture
def test_project(mongodb_archive, tmp_path):
    os.environ[minkipy.ENV_MINKIPY_SETTINGS] = str(tmp_path / 'settings.json')

    project = minkipy.project('minki-tests')
    project.kiwipy['connection_params'] = 'amqp://guest:guest@127.0.0.1'
    project.workon()

    yield project
    mincepy.get_historian()
