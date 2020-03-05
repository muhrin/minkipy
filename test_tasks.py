import io
import logging
import os
from pathlib import Path

import minkipy


def test_load_script():
    script = """\
def add(a, b):
    return a + b
"""
    script_file = io.StringIO(script)
    module = minkipy.load_script(script_file)

    assert module.add(5, 6) == 11


def writing_task(path, msg: str):
    """A simple task that writes a message to a file"""
    with open(str(path), 'w') as file:
        file.write(msg)


def my_task(arg):
    return arg


def test_create_task(test_project):
    # Create a task from a function in a script
    task = minkipy.task(my_task, [5])
    assert isinstance(task, minkipy.Task)
    assert task.run() == 5
    assert task.state == minkipy.DONE

    task2 = minkipy.task("{}@my_task".format(__file__), [10])
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
    assert os.path.isfile(str(tmp_path / folder / Path(__file__).name))


def do_some_logging(level):
    logging.log(level, "I've got some bad news")


def test_task_logging(tmp_path, test_project):
    task = minkipy.task(do_some_logging, (logging.WARNING,), folder='test_task')
    with minkipy.utils.working_directory(tmp_path):
        task.run()
    assert "I've got some bad news" in task.log_file.read_text()

    # Now turn logging off
    task = minkipy.task(do_some_logging, (logging.WARNING,), folder='test_task')
    task.log_level = None
    with minkipy.utils.working_directory(tmp_path):
        task.run()
    assert "I've got some bad news" not in task.log_file.read_text()
