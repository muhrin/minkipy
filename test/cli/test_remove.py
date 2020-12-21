# -*- coding: utf-8 -*-
import minkipy
from minkipy.cli import main

from . import common


def test_remove_simple(cli_runner, test_queue):
    task_1id = test_queue.submit(minkipy.task(common.dummy, args=(500000,)))

    result = cli_runner.invoke(main.remove, [str(task_1id)])
    assert result.exit_code == 0
    assert str(task_1id) in result.output

    # Try removing it again
    result = cli_runner.invoke(main.remove, [str(task_1id)])
    assert result.exit_code == 1
    assert str(task_1id) in result.stderr

    # Now try removing an invalid task
    result = cli_runner.invoke(main.remove, ['made_up_task'])
    assert result.exit_code == 1
    assert 'made_up_task' in result.stderr

    # Remove multiple tasks
    task_1id = test_queue.submit(minkipy.task(common.dummy, args=(500000,)))
    task_2id = test_queue.submit(minkipy.task(common.dummy, args=(500000,)))

    result = cli_runner.invoke(main.remove, [str(task_1id), str(task_2id)])
    assert result.exit_code == 0
    assert str(task_1id) in result.output
    assert str(task_2id) in result.output
