import mincepy

import minkipy


def do_stuff(arg):
    return arg


def test_queue_basic(historian: mincepy.Historian, test_project):
    queue = minkipy.queue('default', historian=historian)
    task = minkipy.task(do_stuff, ['stuff'])
    queue.submit(task)

    with queue.next_task(timeout=2.) as fetched:
        assert fetched.run() == 'stuff'

    # Now check our original 'task' is finished
    task.sync()
    assert task.state == 'done'
