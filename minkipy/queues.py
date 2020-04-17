import contextlib
from typing import Iterator

import kiwipy.rmq
import mincepy

import minkipy
from . import settings
from . import tasks

__all__ = 'Queue', 'queue'

TASK_ID = 'task_id'


class Queue:

    def __init__(self,
                 communicator: kiwipy.rmq.RmqThreadCommunicator,
                 historian,
                 queue_name='default-queue'):
        self._communicator = communicator
        self._historian = historian
        self._kiwi_queue = communicator.task_queue(queue_name)
        self._name = queue_name

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
        """Submit one or more tasks to the queue"""
        for task in tasks:
            self.submit_one(task)

    def submit_one(self, task: tasks.Task):
        """Submit one task to the queue"""
        # Encode the task
        task.save()
        task_id = task.obj_id
        msg = {TASK_ID: task_id}
        self._kiwi_queue.task_send(msg, no_reply=True)
        task.queue = self.name
        task.state = tasks.QUEUED

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
        name = settings.get_default_queue()

    communicator = communicator or settings.get_communicator()
    historian = historian or mincepy.get_historian()
    return Queue(communicator, historian, name)
