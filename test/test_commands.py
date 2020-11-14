# -*- coding: utf-8 -*-
import pathlib
import uuid

import mincepy
from mincepy import testing
import pytest  # pylint: disable=wrong-import-order

import minkipy

# pylint: disable=invalid-name


def simple_wf(obj):
    return obj


class Workflow(mincepy.SimpleSavable):
    TYPE_ID = uuid.UUID('ef45250f-b8b1-46bb-8033-01cd115483a6')

    def add_to_ten(self, value):  # pylint: disable=no-self-use
        return 10 + value


def test_python_command_from_method():
    # Static
    wf = Workflow()
    command = minkipy.command(wf.add_to_ten, args=(1,))  # type: minkipy.PythonCommand
    assert isinstance(command.script_file, mincepy.File)
    assert command.run() == 11

    # CHANGE:
    command = minkipy.command(wf.add_to_ten, args=(1,), dynamic=True)  # type: minkipy.PythonCommand
    assert isinstance(command.script_file, str)
    assert command.run() == 11


def test_python_command_from_module():
    from . import script
    command = minkipy.command(script, args=(3, 254))  # type: minkipy.PythonCommand
    assert isinstance(command.script_file, mincepy.File)
    assert command.run() == 257

    command = minkipy.command(script, args=(3, 254), dynamic=True)  # type: minkipy.PythonCommand
    assert isinstance(command.script_file, str)
    assert command.run() == 257

    # Now try using string instead of the module object
    # Just use some function that we know is importable
    command = minkipy.command('uuid@UUID', args=('61736206-729b-4a0b-9fac-6b5e71123ba0',))
    assert command.run().int == uuid.UUID('61736206-729b-4a0b-9fac-6b5e71123ba0').int


def test_saving_command_args():
    """Test that saving of arguments is handled correctly"""
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


def test_python_command_types():
    """Check that the various ways of creating PythonCommands work"""
    from . import script
    script_path = script.__file__

    # Non dynamic
    cmd = minkipy.PythonCommand(script_path, function='add', args=(5, 10))
    assert isinstance(cmd.script_file, mincepy.File)
    assert cmd.run() == 15

    # Dynamic
    cmd = minkipy.PythonCommand(script_path, function='add', args=(5, 10), dynamic=True)
    assert isinstance(cmd.script_file, str)
    assert cmd.run() == 15

    with pytest.raises(ValueError):
        minkipy.PythonCommand.build(5)


def test_command_saving_basics():
    """Test some basics of loading and saving a command"""
    # Check that older versions without 'dynamic' in their saved state can be loaded
    historian = mincepy.get_historian(create=False)

    from . import script
    script_path = script.__file__

    class CustomPythonCommand(minkipy.PythonCommand):

        def save_instance_state(self, saver):
            state = super().save_instance_state(saver)
            # Pretend we're an older version and have no kwargs or dynamic
            state.pop('_dynamic')
            state.pop('_kwargs')

    cmd = CustomPythonCommand(script_path, function='add', args=(5, 10))

    cmd_id = cmd.save()
    del cmd

    cmd = historian.load(cmd_id)
    assert cmd.kwargs == {}
    assert cmd.dynamic is False
