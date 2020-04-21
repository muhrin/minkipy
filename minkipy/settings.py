import json
import os
from pathlib import Path
from typing import Optional

import click
import kiwipy

__all__ = 'get_communicator', 'settings_path', 'ENV_MINKIPY_SETTINGS'

# pylint: disable=global-statement

ACTIVE_PROJECT_KEY = 'active_project'
ENV_MINKIPY_SETTINGS = 'MINKIPY_SETTINGS'
DEFAULT_SETTINGS = {}

# pylint: disable=invalid-name
_communicator = None


def get_communicator() -> Optional[kiwipy.Communicator]:
    global _communicator
    return _communicator


def set_communicator(communicator: kiwipy.Communicator):
    global _communicator
    _communicator = communicator


def read_settings():
    path = settings_path()
    if not path.exists():
        write_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

    with open(str(path), 'r') as file:
        return json.load(file)


def write_settings(settings: dict):
    path = settings_path()
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(str(settings_path()), 'w') as file:
        json.dump(settings, file, indent=4)


def settings_path():
    try:
        return Path(os.environ[ENV_MINKIPY_SETTINGS])
    except KeyError:
        app_dir = Path(click.get_app_dir('minkipy', roaming=False))
        return app_dir / 'settings.json'
