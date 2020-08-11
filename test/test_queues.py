import minkipy

# pylint: disable=unused-argument


def do_stuff(arg):
    return arg


def test_queue_basic(tmp_path, test_project, queue_name):
    with minkipy.utils.working_directory(tmp_path):
        queue = minkipy.queue(queue_name)
        task = minkipy.task(do_stuff, ['stuff'])
        queue.submit(task)

        with queue.next_task(timeout=2.) as fetched:
            assert fetched.run() == 'stuff'

        # Now check our original 'task' is finished
        task.sync()
        assert task.state == 'done', task.error


def test_queue_iter(test_project, queue_name):
    queue = minkipy.queue(queue_name)

    for idx in range(10):
        task = minkipy.task(do_stuff, [idx])
        queue.submit(task)

    for idx, queued in enumerate(queue):
        assert queued.cmd.args[0] == idx

    assert queue.size() == 10
    queue.purge()
    assert queue.size() == 0


def test_double_submission(test_project, test_queue: minkipy.Queue):
    """Test that you can't submit the same task twice"""
    task = minkipy.task(do_stuff, [None])
    task.save()
    submitted = test_queue.submit(task)
    assert submitted == task.obj_id

    # Should be skipped
    assert not test_queue.submit(task)
