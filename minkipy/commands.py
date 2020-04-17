from abc import ABCMeta, abstractmethod
import inspect
from pathlib import Path
import sys
from typing import List, Optional, Sequence
import uuid

import mincepy
from . import utils

__all__ = 'Command', 'command', 'PythonCommand'


class Command(mincepy.SimpleSavable, metaclass=ABCMeta):
    TYPE_ID = uuid.UUID('38dc3093-058f-4934-9a48-292eeef35e11')
    ATTRS = ('_args',)

    def __init__(self, args: Sequence):
        super().__init__()
        self._args = mincepy.RefList(args)

    @property
    def args(self) -> Sequence:
        return self._args

    @abstractmethod
    def run(self) -> Optional[List]:
        """Run the command with the stored arguments"""

    def copy_files_to(self, path):
        """Copy any command files to the given path"""


def command(cmd, args: Sequence = (), type: str = 'python-function') -> Command:  # pylint: disable=redefined-builtin
    """Create a new command"""
    if type == 'python-function':
        function = 'run'
        if inspect.ismethod(cmd):
            script_file = sys.modules[cmd.__module__].__file__
            function = utils.get_symbol_name(cmd)
            args = (cmd.__self__,) + args
        elif inspect.isfunction(cmd):
            script_file = sys.modules[cmd.__module__].__file__
            function = cmd.__name__
        elif inspect.ismodule(cmd):
            script_file = cmd.__file__
        elif isinstance(cmd, str) and '@' in cmd:
            script_file, function = cmd.split('@')
            if not script_file.endswith('.py'):
                # Assume they've given a module path
                script_file = sys.modules[script_file].__file__
        else:
            raise ValueError("Unknown python function command '{}".format(cmd))

        return PythonCommand(script_file, function, args)

    raise ValueError("Unknown command type '{}'".format(type))


class PythonCommand(Command):
    TYPE_ID = uuid.UUID('61736206-729b-4a0b-9fac-6b5e71123ba0')
    ATTRS = ('_script_file', '_function')

    def __init__(self, script_file, function='run', args=(), historian=None):
        super(PythonCommand, self).__init__(args)
        self._historian = historian or mincepy.get_historian()

        script_file = Path(script_file)
        self._script_file = self._historian.create_file(script_file.name, 'utf-8')
        self._script_file.from_disk(script_file)

        self._function = function

    def __str__(self):
        return "{}@{}{}".format(self._script_file.filename, self._function, self._args)

    @property
    def script_file(self):
        """Access the python script file"""
        return self._script_file

    @property
    def fn_name(self) -> str:
        """The name of the function that will be run in the script"""
        return self._function

    def run(self) -> Optional[List]:
        """Run this python command"""
        with self._script_file.open() as file:
            script = utils.load_script(file)
            run = utils.get_symbol(script, self._function)
            return run(*self._args)

    def copy_files_to(self, path):
        self._script_file.to_disk(path)


HISTORIAN_TYPES = Command, PythonCommand
