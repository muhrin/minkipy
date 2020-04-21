import uuid

import click.testing
import pytest

import minkipy


@pytest.fixture
def cli_runner():
    runner = click.testing.CliRunner()
    yield runner


@pytest.fixture
def second_test_queue():
    queue_name = "test-queue:{}".format(uuid.uuid4())
    queue = minkipy.queue(queue_name)
    yield queue
    queue.purge()
