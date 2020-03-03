from . import tasks
from . import commands
from . import utils


def get_types():
    """Provide a list of all historian types"""
    types = list()
    types.extend(tasks.HISTORIAN_TYPES)
    types.extend(commands.HISTORIAN_TYPES)
    types.extend(utils.HISTORIAN_TYPES)

    return types
