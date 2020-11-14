# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import inspect
from pathlib import Path
import sys
from typing import List, Optional, Sequence, Mapping, Union
import uuid

import mincepy

from . import constants
from . import utils

__all__ = 'Command', 'command', 'PythonCommand'

MODULE_PREFIX = ':mod:'


class Command(mincepy.SimpleSavable, metaclass=ABCMeta):
    TYPE_ID = uuid.UUID('38dc3093-058f-4934-9a48-292eeef35e11')

    def __init__(self, args: Sequence):
        super().__init__()
        self._args = mincepy.RefList(args)

    @mincepy.field('_args')
    def args(self) -> tuple:
        return self._args

    @abstractmethod
    def run(self) -> Optional[List]:
        """Run the command with the stored arguments"""

    def copy_files_to(self, path):
        """Copy any command files to the given path"""


def command(
        cmd,
        args: Sequence = (),
        type: str = 'python-function',  # pylint: disable=redefined-builtin
        **kwargs) -> Command:
    """Command creation factory.

    :param cmd: the command specification, for python function this should be a function or class
        method
    :param args: the (positional) argument for the command
    :param type: the command type, default is 'python-function'
    :param kwargs: additional arguments that will be passed as kwargs to the relevant command class
        constructor so have a look at it's constructor for more details
    """
    if type == 'python-function':
        return PythonCommand.build(cmd, args, **kwargs)

    raise ValueError("Unknown command type '{}'".format(type))


class PythonCommand(Command):
    TYPE_ID = uuid.UUID('61736206-729b-4a0b-9fac-6b5e71123ba0')

    @classmethod
    def build(cls, cmd, args: Sequence = (), dynamic=False, kwargs: dict = None, **rest):
        function = 'run'  # The default function name

        if inspect.ismethod(cmd):
            if dynamic:
                script_file = constants.MODULE_PREFIX + cmd.__module__
            else:
                script_file = sys.modules[cmd.__module__].__file__
            function = utils.get_symbol_name(cmd)
            args = (cmd.__self__,) + args
        elif inspect.isfunction(cmd):
            if dynamic:
                script_file = constants.MODULE_PREFIX + cmd.__module__
            else:
                script_file = sys.modules[cmd.__module__].__file__
            function = cmd.__name__
        elif inspect.ismodule(cmd):
            if dynamic:
                script_file = constants.MODULE_PREFIX + cmd.__name__
            else:
                script_file = cmd.__file__
        elif isinstance(cmd, str) and '@' in cmd:
            script_file, function = cmd.split('@')
            if not script_file.endswith('.py'):
                # Assume they've given a module path
                script_file = sys.modules[script_file].__file__
        else:
            raise ValueError("Unknown python function command '{}".format(cmd))

        return PythonCommand(script_file, function, args, dynamic=dynamic, kwargs=kwargs, **rest)

    # pylint: disable=too-many-arguments
    def __init__(self,
                 script_file,
                 function='run',
                 args=(),
                 kwargs: dict = None,
                 dynamic=False,
                 historian=None):
        """
        Create a python command

        :param script_file: the path to the script file
        :param function: the name of the function in the script file to invoke
        :param args: the arguments to the function
        :param kwargs: the keyword arguments to the function
        :param dynamic: whether to run the function dynamically
            (i.e. import it when the command is ran)
        :param historian: the historian
        """
        super().__init__(args)
        self._historian = historian or mincepy.get_historian()

        if dynamic:
            self._script_file = script_file
        else:
            # Save the script
            script_file = Path(script_file)
            self._script_file = self._historian.create_file(script_file.name, 'utf-8')
            self._script_file.from_disk(script_file)

        self._dynamic = dynamic
        self._function = function
        self._kwargs = mincepy.RefDict(kwargs or {})

    def __str__(self):
        return '{}@{}{}'.format(self._script_file, self._function, self._args)

    @mincepy.field('_dynamic')
    def dynamic(self) -> bool:
        """If True then the task script file will be loaded dynamically and task.script_file will be a string,
        otherwise the file is stored directly in the task."""
        return self._dynamic

    @mincepy.field('_script_file')
    def script_file(self) -> Union[mincepy.File, str]:
        """Access the python script file.
        This can be either a :class:`mincepy.File` if it is stored directly in the task or a string.
        If it is a string it will either be the path to the file or a module path specified as
        ':mod:path.to.module' where 'module' would be imported"""
        return self._script_file

    @mincepy.field('_function')
    def fn_name(self) -> str:
        """The name of the function that will be run in the script"""
        return self._function

    @mincepy.field('_kwargs')
    def kwargs(self) -> Mapping:
        return self._kwargs

    def load_instance_state(self, saved_state, loader: 'mincepy.Loader'):
        super().load_instance_state(saved_state, loader)
        # Deal with new attributes that were added (in case we load an old record)
        if not hasattr(self, '_kwargs'):
            self._kwargs = {}
        if not hasattr(self, '_dynamic'):
            self._dynamic = False

    def run(self) -> Optional[List]:
        """Run this python command"""
        script = utils.load_script(self._script_file)
        run = utils.get_symbol(script, self._function)
        kwargs = self._kwargs or {}
        return run(*self._args, **kwargs)

    def copy_files_to(self, path):
        # Only copy the task file if it is static
        if not self.dynamic:
            self._script_file.to_disk(path)


HISTORIAN_TYPES = Command, PythonCommand
