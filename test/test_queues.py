import minkipy


def do_stuff(arg):
    return arg


def test_queue_basic(tmp_path, test_project):
    with minkipy.utils.working_directory(tmp_path):
        queue = minkipy.queue('default')
        task = minkipy.task(do_stuff, ['stuff'])
        queue.submit(task)

        with queue.next_task(timeout=2.) as fetched:
            assert fetched.run() == 'stuff'

        # Now check our original 'task' is finished
        task.sync()
        assert task.state == 'done', task.error
