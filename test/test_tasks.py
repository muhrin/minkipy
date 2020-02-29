import io

import mincepy

import minkipy


def test_load_script():
    script = """\
def add(a, b):
    return a + b
"""
    script_file = io.StringIO(script)
    module = minkipy.load_script(script_file)

    assert module.add(5, 6) == 11


def my_task(arg):
    return arg


def test_create_task(historian: mincepy.Historian):
    # Create a task from a function in a script
    task = minkipy.task(my_task, [5])
    assert isinstance(task, minkipy.Task)
    assert task.run() == 5

    task2 = minkipy.task("{}@my_task".format(__file__), [10])
    assert task2.run() == 10
