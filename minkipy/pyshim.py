# -*- coding: utf-8 -*-
"""This module acts as a shim to call a python command dynamically i.e. import the file when a
task is ran as opposed to having the function statically stored in the task.

This is useful when you want new tasks to pick up any code changes you make after you submit them

DEV WARNING: Do no change the location, signature or name of run_dynamically as it may break things
for users that have saved tasks (with the current signature)
"""

from minkipy import utils


def run_dynamically(_fn_spec: tuple, *args, **kwargs):
    """Run the given function from the script file passing the args and kwargs and returning the
    result"""
    script_file, function = _fn_spec
    script = utils.load_script(script_file)
    print('Got script {}'.format(script))
    run = utils.get_symbol(script, function)
    print('Got run: {}'.format(run))
    kwargs = kwargs or {}
    return run(*args, **kwargs)
