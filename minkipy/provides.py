"""Extensions to mincePy and the mincePy GUI"""
from typing import Optional, Iterable

import mincepy

from . import projects
from . import queues
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


try:
    from PySide2 import QtWidgets
    import mincepy_gui

except ImportError:
    pass
else:

    class MinkipyActioner(mincepy_gui.Actioner):
        name = "minkipy-actioner"

        SUBMIT = 'Submit'

        def probe(self, obj: object, context: dict) -> Optional[Iterable[str]]:
            if self.is_task_or_task_record(obj) or self.is_collection_of_tasks(obj):
                return [self.SUBMIT]

            return None

        def do(self, action: str, obj: object, context: dict):
            to_submit = []

            def append(item):
                if isinstance(item, mincepy.DataRecord):
                    to_submit.append(mincepy.load(item.obj_id))
                elif isinstance(item, tasks.Task):
                    to_submit.append(item)

            if self.is_task_or_task_record(obj):
                append(obj)
            else:
                # Must be an iterable of tasks
                for entry in obj:
                    append(entry)

            if to_submit:
                queue_name = projects.working_on().default_queue

                parent = context[mincepy_gui.ActionContext.PARENT]
                queue_name, ok = QtWidgets.QInputDialog().getText(  # pylint: disable=invalid-name
                    parent,
                    "Submit task(s)",  # Title
                    "Queue name:",  # Label
                    echo=QtWidgets.QLineEdit.Normal,
                    text=queue_name)

                if ok:
                    if queue_name:
                        queues.queue(queue_name).submit(*to_submit)  # Submit the tasks
                    else:
                        QtWidgets.QMessageBox.warning(parent, "Submit cancelled",
                                                      "Must supply queue name")

        @staticmethod
        def is_task(obj: object) -> bool:
            return isinstance(obj, tasks.Task)

        @staticmethod
        def is_task_record(obj: object) -> bool:
            return isinstance(obj, mincepy.DataRecord) and obj.type_id == tasks.Task.TYPE_ID

        @staticmethod
        def is_task_or_task_record(entry: object) -> bool:
            return MinkipyActioner.is_task(entry) or MinkipyActioner.is_task_record(entry)

        @staticmethod
        def is_collection_of_tasks(obj: object) -> bool:
            # pylint: disable=isinstance-second-argument-not-valid-type
            return isinstance(obj, Iterable) and all(
                map(MinkipyActioner.is_task_or_task_record, obj))


def get_actioners():
    return (MinkipyActioner(),)
