import json
from pathlib import Path
from typing import Optional

import click
import mincepy
import kiwipy

from . import projects

__all__ = 'project', 'get_communicator', 'workon'

ACTIVE_PROJECT_KEY = 'active_project'
DEFAULT_SETTINGS = {}

_communicator = None
_active_project = None


def init_active_project():
    get_active_project().activate()


def get_communicator() -> kiwipy.Communicator:
    global _communicator
    if _communicator is None:
        init_active_project()
    return _communicator


def set_communicator(communicator):
    global _communicator
    _communicator = communicator


def workon(project_name: str = None):
    global _active_project
    if project_name is None:
        settings = read_settings()
        project_name = settings[ACTIVE_PROJECT_KEY]

    proj = get_projects().get(project_name, None)
    if proj is None:
        raise ValueError("Project '{}' does not exist.".format(project_name))

    if _active_project is not None and _active_project.uuid == proj.uuid:
        return

    historian = mincepy.historian(proj.mincepy['connection_params'])
    communicator = kiwipy.connect(proj.kiwipy['connection_params'])

    mincepy.set_historian(historian)
    set_communicator(communicator)
    _active_project = proj


def project(project_name: str = 'default') -> projects.Project:
    settings = read_settings()
    update_settings_file = False

    stored = settings.setdefault('projects', {})

    if project_name not in stored:
        proj = projects.Project(project_name)
        stored[project_name] = proj.to_dict()
        settings.setdefault(ACTIVE_PROJECT_KEY, project_name)
        update_settings_file = True
    else:
        proj = projects.Project.from_dict(stored[project_name])

    if update_settings_file:
        write_settings(settings)

    return proj


def get_active_project() -> Optional[projects.Project]:
    settings = read_settings()
    active = settings.get(ACTIVE_PROJECT_KEY, None)
    if active is None:
        return None

    return projects.Project.from_dict(settings['projects'][active])


def set_active_project(name):
    settings = read_settings()
    if name not in settings['projects']:
        raise ValueError("Project '{}' does not exist".format(name))
    settings[ACTIVE_PROJECT_KEY] = name
    write_settings(settings)


def get_projects() -> dict:
    settings = read_settings()
    return {
        name: projects.Project.from_dict(value)
        for name, value in settings.get('projects', {}).items()
    }


def read_settings():
    path = settings_path()
    if not path.exists():
        write_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

    with open(path, 'r') as fd:
        return json.load(fd)


def write_settings(settings: dict):
    path = settings_path()
    if not path.parent.exists():
        path.mkdir(parents=True, exist_ok=True)

    with open(settings_path(), 'w') as fd:
        json.dump(settings, fd, indent=4)


def settings_path():
    app_dir = Path(click.get_app_dir('minkipy', roaming=False))
    return app_dir / 'settings.json'
