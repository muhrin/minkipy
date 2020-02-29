from . import tasks
from . import commands


def get_types():
    """Provide a list of all historian types"""
    types = list()
    types.extend(tasks.HISTORIAN_TYPES)
    types.extend(commands.HISTORIAN_TYPES)

    return types
