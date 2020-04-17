import pathlib

from mincepy.testing import *

import minkipy


def simple_wf(obj):
    return obj


class Workflow(mincepy.SimpleSavable):
    TYPE_ID = uuid.UUID('ef45250f-b8b1-46bb-8033-01cd115483a6')

    def add_to_ten(self, value):
        return 10 + value


def test_command_from_method(test_project):
    wf = Workflow()
    command = minkipy.command(wf.add_to_ten, args=(1,))
    assert command.run() == 11


def test_saving_command_args(test_project):
    car = Car()
    command = minkipy.command(simple_wf, args=(car,))

    command_id = command.save()
    car_id = car.obj_id

    assert command_id is not None
    assert car_id is not None

    del command

    command = mincepy.load(command_id)
    assert command.args[0].obj_id == car_id


def test_command_none_in_args(test_project):
    """This test checks for a bug where None could not be present in the args
    even though this should be perfectly possible"""
    command = minkipy.command(simple_wf, args=(None,))
    cid = command.save()
    del command

    loaded = mincepy.load(cid)  # type: minkipy.Command
    loaded.run()


def test_load_script_from_file(test_project):
    with minkipy.utils.working_directory(pathlib.Path(__file__).parent):
        cmd = minkipy.command('script.py@add', args=(5, 10))
        assert cmd.run() == 15

        # Try using the abspath now
        script_path = str(pathlib.Path('script.py').resolve())
        cmd = minkipy.command('{}@add'.format(script_path), args=(5, 10))
        assert cmd.run() == 15
