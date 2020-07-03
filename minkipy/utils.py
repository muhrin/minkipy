import contextlib
import importlib.util
import inspect
import io
import os
from pathlib import Path
import re
import shutil
import time
import tempfile
import typing
from typing import Optional, Sequence
import uuid

import mincepy

__all__ = 'ScriptsStore', 'load_script'


def datetime_str() -> str:
    """Get a datetime string that can be used for identifying submissions"""
    return time.strftime("%Y%m%d-%H%M%S")


def get_script_path(script_name):
    script_path = Path(os.path.abspath(os.path.dirname(__file__))) / script_name
    assert os.path.exists(script_name)
    return script_path


class ScriptsStore(mincepy.SimpleSavable):
    TYPE_ID = uuid.UUID('16f09a79-544b-4b43-b1e5-9c62ee1ac99a')
    ATTRS = ('_scripts',)

    def __init__(self, historian=None):
        super().__init__(historian)
        self._scripts = []  # type: typing.MutableSequence[mincepy.builtins.BaseFile]
        self._scripts_namespace = ScriptsNamespace(self)

    @property
    def execute(self):
        """Execute a script"""
        return self._scripts_namespace

    def insert(self, filename):
        """Insert a script"""
        with open(filename, 'rb') as script_file:
            script = self.get(filename)
            if script is None:
                script = self._historian.create_file(filename, 'utf-8')

            with script.open('wb') as script_db:
                shutil.copyfileobj(script_file, script_db)

        self._scripts.append(script)
        self.save()

    def remove(self, filename):
        """Remove a script"""
        for idx, script in enumerate(self._scripts):
            if script.filename == filename:
                del self._scripts[idx]
                return True

        return False

    def get(self, name: str) -> typing.Optional[mincepy.builtins.BaseFile]:
        for script in self._scripts:
            if script.filename == name:
                return script
        return None

    def get_names(self) -> typing.Sequence[str]:
        return [script.filename for script in self._scripts]

    @contextlib.contextmanager
    def open(self, name: str):
        """Open a script by name"""
        with self.get(name).open('r') as file:
            yield file

    def print(self, name):
        """Print a script by name"""
        with self.open(name) as file:
            print(file.read())


class ScriptsNamespace:

    def __init__(self, scripts_store: ScriptsStore):
        self._scripts_store = scripts_store
        self._script_cache = {}

    def __dir__(self) -> typing.Iterable[str]:
        return self._make_script_map().keys()

    def __getattr__(self, item):
        script_name = self._make_script_map()[item]
        try:
            return self._script_cache[script_name]
        except KeyError:
            with self._scripts_store.open(script_name) as file:
                script = load_script(file)
            self._script_cache[script_name] = script
            return script

    def _make_script_map(self):
        return {
            make_valid_python_name(script_name): script_name
            for script_name in self._scripts_store.get_names()
        }

    def _invalidate_cache(self):
        self._script_cache = {}


def make_valid_python_name(string):
    """Convert a filename into a valid python variable name
    Parts borrowed from:
    https://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
    """
    string = Path(string).stem  # Remove extension
    string = string.replace('.', '_')
    string = string.replace('-', '_')

    # Remove invalid characters
    string = re.sub('[^0-9a-zA-Z_]', '', string)

    # Remove leading characters until we find a letter or underscore
    string = re.sub('^[^a-zA-Z_]+', '', string)

    return string


def load_script(script_file: [str, io.TextIOBase]):
    temp_file = None
    script_path = None
    try:
        if isinstance(script_file, io.TextIOBase):
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.py',
                                             delete=False) as temp_file:
                shutil.copyfileobj(script_file, temp_file)
                script_path = temp_file.name
        else:
            script_path = script_file

        spec = importlib.util.spec_from_file_location("script", script_path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)
        return script
    finally:
        if temp_file is not None:
            os.remove(script_path)


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
    return ".".join(yield_symbol_names(symbol))


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

    # TODO: Finish the methods/properties here


@contextlib.contextmanager
def null_context():
    """A context that does nothing"""
    yield


HISTORIAN_TYPES = (ScriptsStore,)
