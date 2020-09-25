import inspect
import os.path
import pathlib

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


def mul(a, b, prefactor=1.):
    return prefactor * a * b


def test_dynamic():
    """Test the dynamic execution of python commands"""
    MODULE_PATH = str(pathlib.Path(__file__).parent / 'test_module.py')
    source = inspect.getsource(mul)

    try:
        with open(MODULE_PATH, 'w') as file:
            file.write(source)

        # pylint: disable=import-outside-toplevel, no-name-in-module
        from . import test_module

        static = minkipy.PythonCommand.build(test_module.mul,
                                             args=(5, 10),
                                             kwargs=dict(prefactor=2.),
                                             dynamic=False)
        dynamic = minkipy.PythonCommand.build(test_module.mul,
                                              args=(5, 10),
                                              kwargs=dict(prefactor=2.),
                                              dynamic=True)

        source = inspect.getsource(add).replace('add', 'mul')
        with open(MODULE_PATH, 'w') as file:
            file.write(source)

        assert static.run() == 100.
        assert dynamic.run() == 30.
    finally:
        os.remove(MODULE_PATH)
