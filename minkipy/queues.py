from contextlib import contextmanager

import mincepy
import kiwipy.rmq

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
        with self._kiwi_queue.next_task(timeout=timeout) as ktask:
            with ktask.processing() as outcome:
                msg = ktask.body
                task = self._historian.load(msg[TASK_ID])  # type: tasks.Task
                task.state = tasks.PROCESSING

                try:
                    yield task
                except Exception as exc:
                    task.error = str(exc)
                    task.state = tasks.FAILED
                    raise
                else:
                    # Task done
                    if task.state == tasks.RUNNING:
                        task.state = tasks.DONE
                    outcome.set_result(True)

    def submit(self, task: tasks.Task):
        """Submit a task to the queue"""
        # Encode the task
        task.save()
        task_id = task.obj_id
        msg = {TASK_ID: task_id}
        self._kiwi_queue.task_send(msg, no_reply=True)
        task.state = tasks.QUEUED


def queue(name: str, communicator=None, historian=None):
    """Get a queue of the given name"""
    communicator = communicator or kiwipy.get_communicator()
    historian = historian or mincepy.get_historian()
    return Queue(communicator, historian, name)
