"""Extensions to mincePy and the mincePy GUI"""
import collections
from typing import Optional, Iterable

import mincepy

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

            if isinstance(obj, Iterable):  # pylint: disable=isinstance-second-argument-not-valid-type
                for entry in obj:
                    append(entry)
            else:
                append(obj)

            if to_submit:
                existing_queues = collections.defaultdict(int)
                for task in to_submit:
                    if task.queue:
                        existing_queues[task.queue] += 1

                queue = ''
                if existing_queues:
                    max_count = max(existing_queues.values())
                    for name, count in existing_queues.items():
                        if count == max_count:
                            queue = name
                            break

                parent = context[mincepy_gui.ActionContext.PARENT]
                queue, ok = QtWidgets.QInputDialog().getText(  # pylint: disable=invalid-name
                    parent,
                    "Submit task(s)",  # Title
                    "Queue name:",  # Label
                    echo=QtWidgets.QLineEdit.Normal,
                    text=queue)

                if ok:
                    if queue:
                        minki_queue = queues.queue(queue)
                        minki_queue.submit(*to_submit)  # Submit the tasks
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
