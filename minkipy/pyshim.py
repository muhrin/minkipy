"""This module acts as a shim to call a python command dynamically i.e. import the file when a
task is ran as opposed to having the function statically stored in the task.

This is useful when you want new tasks to pick up any code changes you make after you submit them
"""

from minkipy import utils


def run_dynamically(script_file: str, function: str, args: tuple = (), kwargs: dict = None):
    """Run the given function from the script file passing the args and kwargs and returning the
    result"""
    script = utils.load_script(script_file)
    print("Got script {}".format(script))
    run = utils.get_symbol(script, function)
    print("Got run: {}".format(run))
    kwargs = kwargs or {}
    return run(*args, **kwargs)
