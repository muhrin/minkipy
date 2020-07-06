from contextlib import contextmanager, redirect_stdout, redirect_stderr
import logging
import os
import uuid
from pathlib import Path
import sys
from typing import List, Sequence

import mincepy

try:
    import pyos
except ImportError:
    pyos = None

from . import commands
from . import utils

__all__ = ('CREATED', 'QUEUED', 'HELD', 'RUNNING', 'DONE', 'FAILED', 'CANCELED', 'TIMEOUT',
           'MEMORY', 'Task', 'task')

# Possible states
CREATED = 'created'
QUEUED = 'queued'
HELD = 'held'
PROCESSING = 'processing'
RUNNING = 'running'
DONE = 'done'
FAILED = 'FAILED'
CANCELED = 'CANCELED'
TIMEOUT = 'TIMEOUT'
MEMORY = 'MEMORY'

STATES = [CREATED, QUEUED, HELD, PROCESSING, RUNNING, DONE, FAILED, CREATED, TIMEOUT, MEMORY]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Task(mincepy.SimpleSavable):
    """A minkiPy task.  This represents a unit of work that can be submitted to a queue."""

    # pylint: disable=too-many-instance-attributes

    TYPE_ID = uuid.UUID('bc48616e-4fcb-41b2-bd03-a37a8fe1dce7')
    ATTRS = ('_cmd', 'folder', '_files', '_state', 'error', 'queue', 'log_level', '_log_file',
             '_stdout', '_stderr', '_pyos_path')

    def __init__(self,
                 cmd: commands.Command,
                 folder: str,
                 files: List[Path] = None,
                 historian=None):
        assert isinstance(folder,
                          str), "Folder name must be a string, got '{}'".format(type(folder))
        super().__init__()
        self._historian = historian or mincepy.get_historian()

        self._cmd = cmd
        self.folder = folder  # The name of the folder where the task will be ran
        self._files = mincepy.builtins.RefList()
        if files:
            for file in files:
                self.add_files(file)
        self._state = CREATED
        self.error = ''
        self.queue = ''  # Set the the name of the queue it's in if it gets put in one
        self.log_level = logging.WARNING
        self._log_file = self._historian.create_file('task_log', encoding='utf-8')
        self._stdout = self._historian.create_file('stdout', encoding='utf-8')
        self._stderr = self._historian.create_file('stderr', encoding='utf-8')

        if pyos is not None:
            self._pyos_path = pyos.os.getcwd()  # type: str
        else:
            self._pyos_path = None

    def __str__(self) -> str:
        str_list = []
        str_list.append("state={}".format(self._state))
        if self.error:
            str_list.append("[{}]".format(self.error))
        return " ".join(str_list)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.save()

    @property
    def cmd(self):
        return self._cmd

    @property
    def files(self) -> Sequence[mincepy.builtins.BaseFile]:
        return self._files

    @property
    def log_file(self) -> mincepy.builtins.BaseFile:
        """Get the log file"""
        return self._log_file

    @property
    def stdout(self) -> mincepy.builtins.BaseFile:
        """Get the standard out file"""
        return self._stdout

    @property
    def stderr(self) -> mincepy.builtins.BaseFile:
        """Get the standard err file"""
        return self._stderr

    @property
    def pyos_path(self):
        if self._pyos_path is None:
            return None

        return pyos.pathlib.PurePath(self._pyos_path)

    @pyos_path.setter
    def pyos_path(self, new_path):
        if new_path is None:
            self._pyos_path = None
        else:
            self._pyos_path = str(new_path)

    # @mincepy.track
    def add_files(self, filename: [str, Path]):
        filename = Path(filename)
        file = self._historian.create_file(filename.name)
        file.from_disk(file)
        self._files.append(file)

    # @mincepy.track
    def run(self):
        with self._capture_log(), self._capture_stds():
            logger.info("Starting task with id %s", self.obj_id)
            if pyos and self.pyos_path is not None:
                path_context = pyos.pathlib.working_path(self.pyos_path)
                logger.debug("Running in pyos path '%s'", self.pyos_path)
            else:
                logger.debug("Running without pyos")
                path_context = utils.null_context()

            with path_context:
                try:
                    self.state = RUNNING
                    if self.folder and not os.path.exists(self.folder):
                        os.makedirs(self.folder)
                    self.copy_files_to(self.folder)

                    # Change the directory to the running folder and back at the end
                    with utils.working_directory(self.folder):
                        result = self._cmd.run()

                    self._state = DONE
                    return result
                except Exception as exc:
                    logger.exception("Task '%s' excepted", self.obj_id)
                    self.error = str(exc)
                    self.state = FAILED
                    raise
                finally:
                    self.save()

    def copy_files_to(self, folder):
        """Copy the task files to the given folder.  The folder must exist already."""
        # For ease of debugging write any command file (e.g. the script file) as well
        # do this first just in case any of the files have a file with the same name
        self.cmd.copy_files_to(folder)
        for file in self._files:
            file.to_disk(folder)

    @contextmanager
    def _capture_log(self):
        """Context handler to enable loggin' on the task"""
        if self.log_level is None:
            # Don't save the log
            yield
            return

        root_logger = logging.getLogger()  # Get the top level logger
        with self.log_file.open('a') as file:
            root_logger.setLevel(self.log_level)
            handler = logging.StreamHandler(file)

            handler.setLevel(self.log_level)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

            # Check if the root logger is currently set to a higher level than the level
            # we want to log at which would mean we don't get the log messages.  If so,
            # temporarily lower it.  See here for an explanation of why this is necessary:
            # https://www.electricmonk.nl/log/2017/08/06/understanding-pythons-logging-module/
            original_root_level = None
            if root_logger.level > self.log_level:
                original_root_level = root_logger
                root_logger.setLevel(self.log_level)

            try:
                root_logger.addHandler(handler)
                yield
            finally:
                root_logger.removeHandler(handler)
                if original_root_level is not None:
                    root_logger.setLevel(original_root_level)

    @contextmanager
    def _capture_stds(self):
        """Capture standard out and err"""
        with self._stdout.open('a') as stdout, self._stderr.open('a') as stderr:
            out = utils.TextMultiplexer(sys.stdout, stdout)
            err = utils.TextMultiplexer(sys.stderr, stderr)
            with redirect_stdout(out), redirect_stderr(err):
                yield


def task(cmd, args=(), folder: str = ''):
    """Create a task"""
    return Task(commands.command(cmd, args), folder)


HISTORIAN_TYPES = (Task,)
