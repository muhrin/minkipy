# -*- coding: utf-8 -*-
import gc
import io
import logging
import os
import pathlib
import sys
from typing import Union

import mincepy
import pytest  # pylint: disable=wrong-import-order

import minkipy
from test import script as script_module  # pylint: disable=wrong-import-order

# pylint: disable=unused-argument, invalid-name, no-member


def test_load_script():
    script = """\
def add(a, b):
    return a + b
"""
    script_file = io.StringIO(script)
    module = minkipy.load_script(script_file)
    assert module.add(5, 6) == 11

    # Test loading by file path
    module = minkipy.load_script(minkipy.constants.FILE_PREFIX + script_module.__file__)
    assert module.add(5, 6) == 11

    # Test loading by import
    module = minkipy.load_script(minkipy.constants.MODULE_PREFIX + script_module.__name__)
    assert module.add(5, 6) == 11

    with pytest.raises(TypeError):
        minkipy.load_script(5)


def writing_task(path, msg: str):
    """A simple task that writes a message to a file"""
    with open(str(path), 'w') as file:
        file.write(msg)


def my_task(arg):
    return arg


def test_create_task(tmp_path, test_project):
    # Create a task from a function in a script
    with minkipy.utils.working_directory(tmp_path):
        task = minkipy.task(my_task, [5])
        assert isinstance(task, minkipy.Task)
        assert task.run() == 5
        assert task.state == minkipy.DONE

        task2 = minkipy.task('{}@my_task'.format(__file__), [10])
        assert task2.run() == 10
        assert task.state == minkipy.DONE


def test_task_working_folder(tmp_path, test_project):
    """Check that a script runs in the folder given"""
    folder = 'task_folder'
    msg = 'Do you have a license for this minki?'
    task = minkipy.task(writing_task, ['hello.txt', msg], folder=folder)

    with minkipy.utils.working_directory(tmp_path):
        task.run()
    assert os.path.exists(str(tmp_path / folder / 'hello.txt'))
    with open(str(tmp_path / folder / 'hello.txt'), 'r') as file:
        assert file.read() == msg


def test_script_written(tmp_path, test_project):
    """Test that a task writes it's script to the folder"""
    folder = 'task_folder'
    task = minkipy.task(my_task, [10], folder=folder)

    with minkipy.utils.working_directory(tmp_path):
        task.run()
    assert os.path.isfile(str(tmp_path / folder / pathlib.Path(__file__).name))


def do_some_logging(level):
    logging.log(level, "I've got some bad news...")


def test_task_logging(tmp_path, test_project):
    task = minkipy.task(do_some_logging, (logging.DEBUG,), folder='test_task')
    task.log_level = logging.DEBUG - 1
    task.save()

    with minkipy.utils.working_directory(tmp_path):
        task.run()

    log_text = task.log_file.read_text()
    assert "I've got some bad news" in log_text
    assert str(task.obj_id) in log_text

    # Now turn logging off
    task = minkipy.task(do_some_logging, (logging.WARNING,), folder='test_task')
    task.log_level = None
    with minkipy.utils.working_directory(tmp_path):
        task.run()
    assert "I've got some bad news" not in task.log_file.read_text()


def show_msg(msg, err=False):
    print(msg, file=sys.stdout if not err else sys.stderr)


def test_task_stds(tmp_path, test_project):
    """Test that tasks can capture standard out and err"""
    with minkipy.utils.working_directory(tmp_path):
        task = minkipy.task(show_msg, args=('Hello stdout!',), folder='test_task')
        task.run()
        assert 'Hello stdout!' in task.stdout.read_text()
        task_id = task.save()

        task2 = minkipy.task(show_msg, args=('Hello stderr!', True), folder='test_task')
        task2.run()
        assert 'Hello stderr!' in task2.stderr.read_text()
        task2_id = task2.save()

        # Make sure they are really stored when saving
        del task, task2
        loaded, loaded2 = mincepy.load(task_id, task2_id)
        assert 'Hello stdout!' in loaded.stdout.read_text()
        assert 'Hello stderr!' in loaded2.stderr.read_text()


def exceptional_task(msg):
    raise RuntimeError(msg)


def test_task_exception(tmp_path, test_project):
    msg = 'all was going well except then the exceptional task excepted'
    task = minkipy.task(exceptional_task, args=(msg,))

    with pytest.raises(RuntimeError):
        task.run()

    assert msg in task.log_file.read_text()


def test_task_resubmit(tmp_path, test_project, test_queue):
    task = minkipy.task(exceptional_task, args=[
        'Arrrgg...',
    ])
    assert task.resubmit() is False

    test_queue.submit(task)

    with test_queue.next_task(timeout=2.) as incoming:
        incoming.run()

    assert task.queue == test_queue.name
    assert task.state == minkipy.FAILED
    assert 'Arrrgg...' in task.error

    task.resubmit()
    assert task.state == minkipy.QUEUED
    assert task in test_queue
    assert not task.error

    with test_queue.next_task(timeout=2.) as incoming:
        incoming.run()

    # Now try resubmitting on different queue (priority)
    priority = minkipy.queue('priority')
    task.resubmit(queue='priority')
    assert task.state == minkipy.QUEUED
    assert task.queue == 'priority'
    assert task in priority
    assert not task.error
    with minkipy.queue('priority').next_task(timeout=2.) as incoming:
        incoming.run()


def add_numbers(filename: Union[str, pathlib.Path]):
    with open(str(filename), 'r') as file:
        numbers = [int(line.rstrip()) for line in file.readlines()]
    return sum(numbers)


def test_task_files(tmp_path, test_project):
    # Have to do this as pytest returns pathlib2 Paths in py<=3.5.  This breaks other parts of the
    # code that expect a pathlib.Path. See:
    # https://github.com/pytest-dev/pytest/issues/5017
    tmp_path = pathlib.Path(str(tmp_path))

    TEST_FILE = tmp_path / 'numbers.dat'
    # Run the task in a subdirectory so it doesn't accidentally pick up the file
    TASK_PATH = tmp_path / 'task'

    with open(str(TEST_FILE), 'w') as file:
        file.write('\n'.join([str(num) for num in range(100)]))

    expected_result = add_numbers(TEST_FILE)

    task = minkipy.Task(minkipy.command(add_numbers, args=(TEST_FILE.name,)),
                        folder=str(TASK_PATH),
                        files=[TEST_FILE])
    assert len(task.files) == 1
    assert task.files[0].filename == TEST_FILE.name  # pylint: disable=unsubscriptable-object
    assert task.run() == expected_result

    # Now try adding the files manually
    task = minkipy.Task(
        minkipy.command(add_numbers, args=(TEST_FILE.name,)),
        folder=str(TASK_PATH),
    )
    task.add_files(TEST_FILE)
    assert len(task.files) == 1
    assert task.files[0].filename == TEST_FILE.name  # pylint: disable=unsubscriptable-object
    assert task.run() == expected_result


def test_task_parameters(test_project):
    """Make sure that the task() helper create the task correctly"""
    task = minkipy.task(my_task,
                        args=(1, 2, 3),
                        kwargs=dict(kword='this'),
                        dynamic=True,
                        folder='some_folder',
                        files=(__file__,))
    assert isinstance(task.cmd, minkipy.PythonCommand)
    assert task.cmd.dynamic is True
    assert tuple(task.cmd.args) == (1, 2, 3)
    assert task.cmd.kwargs == dict(kword='this')
    assert task.folder == 'some_folder'
    assert task.files[0].filename == os.path.basename(__file__)  # pylint: disable=unsubscriptable-object

    # Now make sure we can save the task with all parameters
    task_id = task.save()
    del task
    gc.collect()

    # Load and check
    task = mincepy.load(task_id)
    assert isinstance(task.cmd, minkipy.PythonCommand)
    assert task.cmd.dynamic is True
    assert tuple(task.cmd.args) == (1, 2, 3)
    assert task.cmd.kwargs == dict(kword='this')
    assert task.folder == 'some_folder'
    assert task.files[0].filename == os.path.basename(__file__)  # pylint: disable=unsubscriptable-object
