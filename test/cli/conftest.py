# -*- coding: utf-8 -*-
import uuid

import click.testing
import pytest

import minkipy


@pytest.fixture
def cli_runner():
    runner = click.testing.CliRunner(mix_stderr=False)
    yield runner


@pytest.fixture
def second_test_queue():
    queue_name = 'test-queue:{}'.format(uuid.uuid4())
    queue = minkipy.queue(queue_name)
    yield queue
    queue.purge()
