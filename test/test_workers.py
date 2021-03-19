# -*- coding: utf-8 -*-
import minkipy


def add(val1, val2):
    return val1 + val2


def test_create_task(tmp_path, test_project, queue_name):  # pylint: disable=unused-argument
    with minkipy.utils.working_directory(tmp_path):
        test_queue = minkipy.queue(queue_name)
        task1 = minkipy.task(add, (4, 5))
        task2 = minkipy.task(add, (24, 56))
        test_queue.submit(task1, task2)

        minkipy.run(test_queue, 2)

        assert task1.state == minkipy.DONE
        assert task2.state == minkipy.DONE


def test_empty(test_project, queue_name):  # pylint: disable=unused-argument
    test_queue = minkipy.queue(queue_name)
    assert minkipy.run(test_queue) == 0
