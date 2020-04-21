import minkipy


def add(a, b):
    return a + b


def test_create_task(tmp_path, test_project, queue_name):
    with minkipy.utils.working_directory(tmp_path):
        test_queue = minkipy.queue(queue_name)
        t1 = minkipy.task(add, (4, 5))
        t2 = minkipy.task(add, (24, 56))
        test_queue.submit(t1, t2)

        minkipy.run(test_queue, 2)

        assert t1.state == minkipy.DONE
        assert t2.state == minkipy.DONE


def test_empty(test_project, queue_name):
    test_queue = minkipy.queue(queue_name)
    assert minkipy.run(test_queue) == 0
