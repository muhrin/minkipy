import kiwipy

from . import queues

__all__ = ('run',)


def run(queue: queues.Queue, max_tasks: int = -1, timeout=60.) -> int:
    """
    Process a number of tasks from the given queue

    :param queue: the queue to process tasks from
    :param max_tasks: the maximum number of tasks to process
    :param timeout: the maximum time (in seconds) to wait for a new task
    """
    num_processed = 0
    try:
        while True:
            with queue.next_task(timeout=timeout) as fetched:
                fetched.run()
            num_processed += 1
            if max_tasks > 0 and num_processed >= max_tasks:
                return num_processed
    except kiwipy.QueueEmpty:
        return num_processed
