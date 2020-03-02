import uuid


class Project:

    def __init__(self, name: str):
        """Create a new project"""
        self.name = name
        self._uuid = uuid.uuid4()
        # Kiwipy settings
        self.kiwipy = {'connection_params': 'amqp://guest:guest@127.0.0.1/{}'.format(name)}
        # Mincepy settings
        self.mincepy = {'connection_params': 'mongodb://127.0.0.1/{}'.format(name)}

    @property
    def uuid(self) -> uuid.UUID:
        return self._uuid

    @classmethod
    def from_dict(cls, project_dict):
        project = Project.__new__(Project)

        project.name = project_dict['name']
        project.kiwipy = project_dict['kiwipy']
        project.mincepy = project_dict['mincepy']
        project._uuid = uuid.UUID(project_dict['uuid'])

        return project

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'uuid': str(self.uuid),
            'kiwipy': self.kiwipy,
            'mincepy': self.mincepy,
        }
