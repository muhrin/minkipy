import io
import os

import minkipy


def test_load_script():
    script = """\
def add(a, b):
    return a + b
"""
    script_file = io.StringIO(script)
    module = minkipy.load_script(script_file)

    assert module.add(5, 6) == 11


def writing_task(path, msg):
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
    msg = 'Do you have a license for this minki?'
    task = minkipy.task(writing_task, ['hello.txt', msg], folder=tmp_path)
    task.run()
    assert os.path.exists(tmp_path / 'hello.txt')
    with open(str(tmp_path / 'hello.txt'), 'r') as file:
        assert file.read() == msg
