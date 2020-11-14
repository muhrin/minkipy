# -*- coding: utf-8 -*-
import contextlib
import functools
import importlib.machinery
import importlib.util
import inspect
import io
import os
from pathlib import Path
import shutil
import tempfile
import types
from typing import Optional, Sequence

import mincepy

from . import constants

__all__ = ('load_script',)


@functools.singledispatch
def load_script(script_file: [str, io.TextIOBase]) -> types.ModuleType:
    """Load a module from the given script file.

    The script file can be an io.TextIOBase in which case it will be saved and loaded directly.
    If it is a mincepy.File it will be opened and loaded.
    If it is a string it will be interpreted as follows:
        * If is starts with :mod:... it will be treated as a module
        * If it starts with :file:... the file will be loaded as a module
        * Otherwise the string is treated as a file path as if it were prefixed with :file:
    """
    raise TypeError('Unknown script file type: {}'.format(script_file.__class__.__name__))


@load_script.register(str)
def _(script_file: str) -> types.ModuleType:
    if script_file.startswith(constants.MODULE_PREFIX):
        mod_name = script_file[len(constants.MODULE_PREFIX):]
        return importlib.import_module(mod_name)

    if script_file.startswith(constants.FILE_PREFIX):
        script_file = script_file[len(constants.FILE_PREFIX):]

    # Ok, assume that the string _is_ the script itself
    spec = importlib.util.spec_from_file_location('script', script_file)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    return script


@load_script.register(io.TextIOBase)
def _(script_file: io.TextIOBase) -> types.ModuleType:
    temp_file = None
    script_path = None
    try:
        # Save to a temporary file
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.py',
                                         delete=False) as temp_file:
            shutil.copyfileobj(script_file, temp_file)
            script_path = temp_file.name

        return load_script(constants.FILE_PREFIX + script_path)
    finally:
        if temp_file is not None:
            os.remove(script_path)


@load_script.register(mincepy.File)
def _(script_file: mincepy.File) -> types.ModuleType:
    with script_file.open('r') as file:
        return load_script(file)


def get_symbol(module, name: str):
    """Given a module and a string that represents a path to a symbol this will retrieve it
    e.g. name='MyClass.do_stuff' will get the do_stuff function from the class MyClass within
    the module 'module'"""
    path = name.split('.')
    obj = module
    for entry in path:
        obj = getattr(obj, entry)
    return obj


def yield_symbol_names(symbol):
    if inspect.ismethod(symbol) or inspect.isfunction(symbol):
        if inspect.ismethod(symbol):
            yield from yield_symbol_names(symbol.__self__)
        yield symbol.__name__
    elif isinstance(symbol, object):
        yield symbol.__class__.__name__
    else:
        raise TypeError("Unknown symbol type: '{}'".format(symbol))


def get_symbol_name(symbol):
    return '.'.join(yield_symbol_names(symbol))


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    if path:
        os.chdir(str(path))  # str call for python < 3.6
    try:
        yield
    finally:
        os.chdir(str(prev_cwd))


class TextMultiplexer(io.TextIOBase):
    """Takes a primary output stream and sends all write command to it and all the secondary
    streams.  Otherwise behaves like the primary stream.
    """

    def __init__(self, primary, *secondary):
        super().__init__()
        self._primary = primary  # type: io.TextIOBase
        self._secondary = secondary  # type: Sequence[io.TextIOBase]

    # Deliberately don't implement close!

    @property
    def closed(self):
        return self._primary.closed

    @property
    def encoding(self):
        return self._primary.encoding

    @property
    def errors(self):
        return self._primary.errors

    def fileno(self) -> int:
        return self._primary.fileno()

    def flush(self) -> None:
        return self._primary.flush()

    def isatty(self) -> bool:
        return self._primary.isatty()

    @property
    def mode(self):
        return self._primary.mode

    @property
    def name(self):
        return self._primary.name

    def writable(self) -> bool:
        return self._primary.writable()

    @property
    def newlines(self):
        return self._primary.newlines

    def next(self):
        return self._primary.next()

    def read(self, size: Optional[int] = ...) -> str:
        return self._primary.read(size)

    def write(self, s: str):
        self._primary.write(s)
        for stream in self._secondary:
            stream.write(s)


HISTORIAN_TYPES = tuple()
