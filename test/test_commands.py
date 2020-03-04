import uuid

import mincepy

import minkipy


def print_wf(obj):
    print(obj)


class Workflow(mincepy.BaseSavableObject):
    TYPE_ID = uuid.UUID('ef45250f-b8b1-46bb-8033-01cd115483a6')

    def add_to_ten(self, value):
        return 10 + value


def test_command_from_method(test_project):
    wf = Workflow()
    command = minkipy.command(wf.add_to_ten, args=(1,))
    assert command.run() == 11


def test_saving_command_args(test_project):
    car = mincepy.testing.Car()
    command = minkipy.command(print_wf, args=(car,))

    command_id = command.save()
    car_id = car.obj_id

    assert command_id is not None
    assert car_id is not None

    del command

    command = mincepy.load(command_id)
    assert command.args[0].obj_id == car_id
