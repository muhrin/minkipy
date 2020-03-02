from contextlib import contextmanager

import kiwipy.rmq
import mincepy

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

    def __iter__(self):
        for msg in self._kiwi_queue:
            yield self._historian.load(msg.body[TASK_ID])

    @contextmanager
    def next_task(self, timeout=None):
        with self._kiwi_queue.next_task(timeout=timeout, fail=False) as ktask:
            with ktask.processing() as outcome:
                msg = ktask.body
                task = self._historian.load(msg[TASK_ID])  # type: tasks.Task
                task.state = tasks.PROCESSING

                try:
                    yield task
                    # Task done
                    if task.state == tasks.RUNNING:
                        task.state = tasks.DONE
                except Exception as exc:
                    outcome.set_exception(exc)
                else:
                    outcome.set_result(True)

    def submit(self, task, *tasks):
        """Submit one or more tasks to the queue"""
        self.submit_one(task)
        for additional in tasks:
            self.submit_one(additional)

    def submit_one(self, task: tasks.Task):
        """Submit one task to the queue"""
        # Encode the task
        task.save()
        task_id = task.obj_id
        msg = {TASK_ID: task_id}
        self._kiwi_queue.task_send(msg, no_reply=True)
        task.state = tasks.QUEUED


def queue(name: str, communicator=None, historian=None):
    """Get a queue of the given name"""
    communicator = communicator or settings.get_communicator()
    historian = historian or mincepy.get_historian()
    return Queue(communicator, historian, name)
