# -*- coding: utf-8 -*-
import minkipy
from minkipy.cli import main

from . import common


def test_list_simple(cli_runner, test_queue):
    task_1id = test_queue.submit(minkipy.task(common.dummy, args=(500000,)))
    task_2id = test_queue.submit(minkipy.task(common.dummy, args=('hello',)))

    result = cli_runner.invoke(main.list, [test_queue.name])
    assert result.exit_code == 0
    assert str(task_1id) in result.output
    assert str(task_2id) in result.output

    assert common.dummy.__name__ in result.output
    assert str(500000) in result.output
    assert str('hello') in result.output


def test_list_default(cli_runner):
    default_queue = minkipy.queue()
    task_id = default_queue.submit(minkipy.task(common.dummy, args=('hello',)))

    result = cli_runner.invoke(main.list)
    assert result.exit_code == 0
    assert str(task_id) in result.output
    assert common.dummy.__name__ in result.output
    assert str('hello') in result.output


def test_multiqueue_list(cli_runner, test_queue):
    queue = minkipy.queue()

    task_1id = queue.submit(minkipy.task(common.dummy, args=(500000,)))
    task_2id = test_queue.submit(minkipy.task(common.dummy, args=('hello',)))

    result = cli_runner.invoke(main.list, [queue.name, test_queue.name])
    assert result.exit_code == 0
    assert str(queue.name) in result.output
    assert str(test_queue.name) in result.output

    assert str(task_1id) in result.output
    assert str(task_2id) in result.output

    assert common.dummy.__name__ in result.output
    assert str(500000) in result.output
    assert str('hello') in result.output


def test_list_count(cli_runner, test_queue):
    task1_id = test_queue.submit(minkipy.task(common.dummy, args=(500000,)))
    test_queue.submit(minkipy.task(common.dummy, args=('hello',)))

    result = cli_runner.invoke(main.list, ['-c', test_queue.name])
    assert result.exit_code == 0
    assert 'total: 2' in result.output
    assert 'Empty' not in result.output
    assert str(task1_id) not in result.output

    test_queue.purge()
    result = cli_runner.invoke(main.list, ['-c', test_queue.name])
    assert result.exit_code == 0
    assert 'total' not in result.output
    assert 'Empty' in result.output
    assert str(task1_id) not in result.output
