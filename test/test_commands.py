import uuid

import mincepy

import minkipy


class Workflow(mincepy.BaseSavableObject):
    TYPE_ID = uuid.UUID('ef45250f-b8b1-46bb-8033-01cd115483a6')

    def add_to_ten(self, value):
        return 10 + value


def test_command_from_method(test_project):
    wf = Workflow()
    command = minkipy.command(wf.add_to_ten, args=(1,))
    assert command.run() == 11
