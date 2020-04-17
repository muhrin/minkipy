# Test pyos related functionality

import pytest

# Skip these tests if pyos is not installed
pyos = pytest.importorskip("pyos")  # pylint: disable=invalid-name
import pyos.pyos
from mincepy.testing import Car

import minkipy


def car_maker():
    return Car().save()


def test_pyos_path_default(tmp_path, test_project):
    # Create a task from a function in a script
    cwd = pyos.pyos.pwd()
    with minkipy.utils.working_directory(tmp_path):
        task = minkipy.task(car_maker)
        assert task.pyos_path == cwd
        car_id = task.run()
        # Now look for the car
        results = pyos.pyos.ls(car_id)
        assert len(results) == 1
        assert results[0].obj_id == car_id
        assert isinstance(pyos.pyos.load(results[0]), Car)


def test_pyos_path_custom(tmp_path, test_project):
    # Create a task from a function in a script
    task_path = pyos.Path('work/here/')
    with minkipy.utils.working_directory(tmp_path):
        task = minkipy.task(car_maker)
        task.pyos_path = task_path

        car_id = task.run()
        # Now look for the car
        results = pyos.pyos.ls(task_path / str(car_id))
        assert len(results) == 1
        assert results[0].obj_id == car_id
        assert isinstance(pyos.pyos.load(results[0]), Car)
