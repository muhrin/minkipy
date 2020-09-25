import os.path

import minkipy

# pylint: disable=invalid-name


def add(a, b, prefactor=1.):
    return prefactor * (a + b)


def test_basics():
    cmd = minkipy.PythonCommand.build(add, args=(5, 10), kwargs=dict(prefactor=2.))
    assert cmd.fn_name == 'add'
    assert cmd.script_file.filename == os.path.basename(__file__)
    assert cmd.run() == 30
    assert cmd.run() == 30, "Just making sure we can run multiple times"
