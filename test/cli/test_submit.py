# -*- coding: utf-8 -*-
import click.testing

import minkipy
from minkipy.cli import main

from . import common


def submit_simple(cli_runner: click.testing.CliRunner):
    queue = minkipy.queue()
    assert queue.size() == 0

    result = cli_runner.invoke(main.submit,
                               ['{}@{}'.format(common.__file__, common.simple.__name__)])
    assert result.exit_code == 0

    queue = minkipy.queue()
    assert queue.size() == 1

    with queue.next_task(timeout=0.5) as task:
        assert isinstance(task.cmd, minkipy.PythonCommand)
        assert task.cmd.script_file.filename == common.__file__
        assert task.cmd.fn_name == common.simple.__name__
