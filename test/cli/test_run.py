import click.testing

import minkipy
from minkipy.cli import main

from . import common


def test_run_default_queue(cli_runner: click.testing.CliRunner):
    task = minkipy.task(common.simple, [5])
    queue = minkipy.queue()
    assert queue.size() == 0, "Queue '{}' not empty!".format(queue.name)
    queue.submit(task)
    assert queue.size() == 1

    result = cli_runner.invoke(main.run, ['-n 1'])
    assert result.exit_code == 0

    assert task.state == minkipy.DONE
