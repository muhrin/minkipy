import collections
import contextlib
import functools
from typing import Iterator, Any, Sequence, Dict

import kiwipy.rmq
import mincepy

try:
    import pyos
except ImportError:
    pyos = None
import tabulate

import minkipy  # pylint: disable=unused-import
from . import projects
from . import settings
from . import tasks

__all__ = 'Queue', 'queue'

TASK_ID = 'task_id'


class Queue:
    """A task queue"""

    def __init__(self,
                 communicator: kiwipy.rmq.RmqThreadCommunicator,
                 historian,
                 queue_name='default-queue'):
        self._communicator = communicator
        self._historian = historian
        self._kiwi_queue = communicator.task_queue(queue_name)
        self._name = queue_name

    def size(self):
        count = 0
        for _ in self._kiwi_queue:
            count += 1
        return count

    def __iter__(self) -> Iterator[tasks.Task]:
        """Iterate through the tasks in this queue in the order they were submitted"""
        for msg in self._kiwi_queue:
            yield self._historian.load(msg.body[TASK_ID])

    def __str__(self) -> str:
        """Get the name of this queue"""
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def empty(self) -> bool:
        return self._kiwi_queue.next_task(timeout=0, false=False) is None

    def list(self, verbosity: int = 1):
        """Pretty-print the list of tasks."""
        pprint(tuple(self), verbosity)

    @contextlib.contextmanager
    def next_task(self, timeout=None):
        with self._kiwi_queue.next_task(timeout=timeout) as ktask:
            with ktask.processing() as outcome:
                msg = ktask.body
                task = self._historian.load(msg[TASK_ID])  # type: tasks.Task
                task.state = tasks.PROCESSING

                try:
                    yield task
                    # Task done
                    if task.state == tasks.RUNNING:
                        task.state = tasks.DONE
                except Exception as exc:  # pylint: disable=broad-except
                    outcome.set_exception(exc)
                else:
                    outcome.set_result(True)
                finally:
                    task.queue = ''

    def submit(self, *tasks: 'minkipy.Task'):  # pylint: disable=redefined-outer-name
        """Submit one or more tasks to the queue.  The task ids will be returned."""
        task_ids = []
        for task in tasks:
            task_ids.append(self.submit_one(task))

        if len(tasks) == 1:
            return task_ids[0]

        return task_ids

    def submit_one(self, task: tasks.Task) -> Any:
        """Submit one task to the queue.  The object id for the task will be returned."""
        # Encode the task
        task.save()
        task_id = task.obj_id
        msg = {TASK_ID: task_id}
        self._kiwi_queue.task_send(msg, no_reply=True)
        task.queue = self.name
        task.state = tasks.QUEUED
        return task_id

    def purge(self) -> int:
        """Cancel all tasks in this queue"""
        num_cancelled = 0
        for ktask in self._kiwi_queue:
            with ktask.processing() as outcome:
                task = self._historian.load(ktask.body[TASK_ID])  # type: tasks.Task
                # There is a bug in kiwipy that prevents us from cancelling this future so
                # for now just set a cancelled results.  In any case the result is not sent
                # back for the time being.
                outcome.set_result('Cancelled')
            task.state = tasks.CANCELED
            num_cancelled += 1

        return num_cancelled


def queue(name: str = None,
          communicator: kiwipy.Communicator = None,
          historian: mincepy.Historian = None):
    """Get a queue of the given name.  If the queue doesn't exist it will be
    created.  If None is passed the default queue will be used.

    """
    if name is None:
        name = projects.working_on().default_queue

    communicator = communicator or settings.get_communicator()
    historian = historian or mincepy.get_historian()
    return Queue(communicator, historian, name)


def pprint(tasks_list: Sequence[tasks.Task], verbosity: int = 2) -> None:
    """Pretty print information about tasks"""
    if verbosity < 0:
        return

    if not tasks_list:
        print("Empty")
        return

    headers = ['obj_id', 'cmd', 'state', 'error']

    def fetch(name, obj, transform=str):
        return transform(getattr(obj, name))

    # Create the getter functions that will fetch the data
    getters = [functools.partial(fetch, col) for col in headers]
    if pyos is not None:
        headers.insert(1, 'pyos_path')
        getters.insert(1, functools.partial(fetch, 'pyos_path', transform=pyos.os.path.relpath))

    rows = []
    state_counts = collections.defaultdict(int)  # type: Dict[str, int]
    for task in tasks_list:
        row = []
        for getter in getters:
            value = getter(task)
            row.append(value)
        state_counts[task.state] += 1
        rows.append(row)

    if verbosity >= 1:
        print(tabulate.tabulate(rows, headers=headers if verbosity else None))

    state_counts['total'] = len(tasks_list)
    print(', '.join("{}: {}".format(state, count) for state, count in state_counts.items()))
