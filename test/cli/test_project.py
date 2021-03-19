# -*- coding: utf-8 -*-
import minkipy
from minkipy.cli import project


def test_project_list(cli_runner):
    active_project = minkipy.get_active_project()
    result = cli_runner.invoke(project.list)

    assert result.exit_code == 0
    assert str(active_project.name) in result.output
    assert str(minkipy.settings_path()) in result.output
