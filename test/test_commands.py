# -*- coding: utf-8 -*-
import pathlib
import uuid

import mincepy
from mincepy import testing
import pytest

import minkipy

# pylint: disable=invalid-name


def simple_wf(obj):
    return obj


class Workflow(mincepy.SimpleSavable):
    TYPE_ID = uuid.UUID('ef45250f-b8b1-46bb-8033-01cd115483a6')

    def add_to_ten(self, value):  # pylint: disable=no-self-use
        return 10 + value


def test_python_command_from_method():
    wf = Workflow()
    command = minkipy.command(wf.add_to_ten, args=(1,))
    assert command.run() == 11


def test_python_command_from_module():
    from . import script
    command = minkipy.command(script, args=(3, 254))
    assert command.run() == 257

    # Now try using string instead of the module object
    # Just use some function that we know is importable
    command = minkipy.command('uuid@UUID', args=('61736206-729b-4a0b-9fac-6b5e71123ba0',))
    assert command.run().int == uuid.UUID('61736206-729b-4a0b-9fac-6b5e71123ba0').int


def test_saving_command_args():
    car = testing.Car()
    command = minkipy.command(simple_wf, args=(car,))

    command_id = command.save()
    car_id = car.obj_id

    assert command_id is not None
    assert car_id is not None

    del command

    command = mincepy.load(command_id)
    assert command.args[0].obj_id == car_id


def test_command_none_in_args():
    """This test checks for a bug where None could not be present in the args
    even though this should be perfectly possible"""
    command = minkipy.command(simple_wf, args=(None,))
    cid = command.save()
    del command

    loaded = mincepy.load(cid)  # type: minkipy.Command
    loaded.run()


def test_load_script_from_file():
    with minkipy.utils.working_directory(pathlib.Path(__file__).parent):
        cmd = minkipy.command('script.py@add', args=(5, 10))
        assert cmd.run() == 15

        # Try using the abspath now
        script_path = str(pathlib.Path('script.py').resolve())
        cmd = minkipy.command('{}@add'.format(script_path), args=(5, 10))
        assert cmd.run() == 15


def test_invalid_command():
    with pytest.raises(ValueError):
        minkipy.command('bla', type='made up')
