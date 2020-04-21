from typing import Optional
import uuid

try:
    import pyos
except ImportError:
    pyos = None

import kiwipy
import mincepy

from . import settings

__all__ = ('Project', 'workon', 'project', 'working_on', 'get_active_project', 'set_active_project',
           'get_projects')

# pylint: disable=global-statement, redefined-outer-name

# pylint: disable=invalid-name
_working_on = None  # type: Optional[Project]
PROJECTS_KEY = 'projects'


def _make_default_queue_name(project_name) -> str:
    return "{}-default-queue".format(project_name)


class Project:

    def __init__(self, name: str):
        """Create a new project"""
        self.name = name
        self._uuid = uuid.uuid4()
        # Kiwipy settings
        self.kiwipy = {'connection_params': 'amqp://guest:guest@127.0.0.1/{}'.format(name)}
        # Mincepy settings
        self.mincepy = {'connection_params': 'mongodb://127.0.0.1/{}'.format(name)}
        self.default_queue = _make_default_queue_name(name)

    def __repr__(self) -> str:
        return "Project('{}')".format(self.name)

    @property
    def uuid(self) -> uuid.UUID:
        return self._uuid

    @classmethod
    def from_dict(cls, project_dict):
        # pylint: disable=protected-access
        project = Project.__new__(Project)

        project.name = project_dict['name']
        project.kiwipy = project_dict['kiwipy']
        project.mincepy = project_dict['mincepy']
        project._uuid = uuid.UUID(project_dict['uuid'])
        project.default_queue = project_dict.get('default_queue',
                                                 _make_default_queue_name(project.name))

        return project

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'uuid': str(self.uuid),
            'kiwipy': self.kiwipy,
            'mincepy': self.mincepy,
            'default_queue': self.default_queue
        }

    def workon(self):
        historian = mincepy.create_historian(self.mincepy['connection_params'])
        kiwi_params = self.kiwipy['connection_params']
        if isinstance(kiwi_params, str):
            comm = kiwipy.connect(kiwi_params)
        elif isinstance(kiwi_params, dict):
            comm = kiwipy.connect(**kiwi_params)
        else:
            raise ValueError(
                "kiwi parameters must be string or dictionary, got '{}'".format(kiwi_params))
        settings.set_communicator(comm)

        mincepy.set_historian(historian)
        if pyos is not None:
            pyos.lib.init()

        _set_working_on(self)

    def save(self):
        """Save the project to the settings file"""
        settings_dict = settings.read_settings()
        settings_dict[PROJECTS_KEY][self.name] = self.to_dict()
        settings.write_settings(settings_dict)

    def set_as_active(self):
        settings_dict = settings.read_settings()
        # Make sure we're up to date
        settings_dict[PROJECTS_KEY][self.name] = self.to_dict()
        settings_dict[settings.ACTIVE_PROJECT_KEY] = self.name
        settings.write_settings(settings_dict)


def get_projects() -> dict:
    settings_dict = settings.read_settings()
    return {
        name: Project.from_dict(value) for name, value in settings_dict.get('projects', {}).items()
    }


def project(project_name: str = 'default') -> Project:
    """Fetch a project with a given name or create a new one"""
    settings_dict = settings.read_settings()
    update_settings_file = False

    stored = settings_dict.setdefault('projects', {})

    if project_name not in stored:
        proj = Project(project_name)
        stored[project_name] = proj.to_dict()
        settings_dict.setdefault(settings.ACTIVE_PROJECT_KEY, project_name)
        update_settings_file = True
    else:
        proj = Project.from_dict(stored[project_name])

    if update_settings_file:
        settings.write_settings(settings_dict)

    return proj


def workon(project_name: str = None, auto_create=False) -> Optional[Project]:
    """
    Set the project currently being worked on.  This will set the global historian and kiwipy
    communicator so be careful if you were already using these.

    :param project_name: the project to work on.  If None, will use the currently active project
    :param auto_create: if True automatically create a project if it doesn't exist
    """
    global _working_on
    if project_name is None:
        settings_dict = settings.read_settings()
        project_name = settings_dict[settings.ACTIVE_PROJECT_KEY]

    proj = get_projects().get(project_name, None)
    if proj is None:
        if auto_create:
            proj = project(project_name)
        else:
            raise ValueError("Project '{}' does not exist.".format(project_name))

    if _working_on is not None and _working_on.uuid == proj.uuid:
        return proj

    proj.workon()
    return proj


def working_on() -> Project:
    global _working_on
    if _working_on is None:
        workon()
    return _working_on


def get_active_project() -> Optional[Project]:
    """Gets the currently active project from the settings.  This may be not be the project
    currently being worked on"""
    settings_dict = settings.read_settings()
    active = settings_dict.get(settings.ACTIVE_PROJECT_KEY, None)
    if active is None:
        return None

    return Project.from_dict(settings_dict['projects'][active])


def set_active_project(name):
    """Set the currently active project in the settings"""
    settings_dict = settings.read_settings()
    if name not in settings_dict['projects']:
        raise ValueError("Project '{}' does not exist".format(name))
    settings_dict[settings.ACTIVE_PROJECT_KEY] = name
    settings.write_settings(settings_dict)


def _set_working_on(project: Project):
    global _working_on
    _working_on = project


def _get_working_on() -> Project:
    global _working_on
    return _working_on
