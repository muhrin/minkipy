import uuid
import os
from pathlib import Path
from typing import List, Sequence

import mincepy

from . import commands

__all__ = ('QUEUED', 'HELD', 'RUNNING', 'DONE', 'FAILED', 'CANCELED', 'TIMEOUT', 'MEMORY', 'Task',
           'task')

# Possible states
QUEUED = 'queued'
HELD = 'held'
PROCESSING = 'processing'
RUNNING = 'running'
DONE = 'done'
FAILED = 'FAILED'
CANCELED = 'CANCELED'
TIMEOUT = 'TIMEOUT'
MEMORY = 'MEMORY'


class Task(mincepy.BaseSavableObject):
    TYPE_ID = uuid.UUID('bc48616e-4fcb-41b2-bd03-a37a8fe1dce7')
    ATTRS = ('_cmd', 'folder', '_files', '_state', 'error')

    def __init__(self,
                 cmd: commands.Command,
                 folder: Path,
                 files: List[Path] = None,
                 historian=None):
        super().__init__(historian)
        self._cmd = cmd
        self.folder = folder  # The name folder where the task will be ran
        self._files = mincepy.builtins.RefList()
        if files:
            for file in files:
                self.add_files(file)
        self._state = ''
        self.error = ''

    @property
    def state(self):
        self.sync()
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.save()

    @property
    def files(self) -> Sequence[mincepy.builtins.BaseFile]:
        return self._files

    # @mincepy.track
    def add_files(self, filename: [str, Path]):
        filename = Path(filename)
        file = self._historian.create_file(filename.name)
        file.from_disk(file)
        self._files.append(file)

    # @mincepy.track
    def run(self):
        try:
            self.state = RUNNING
            if not os.path.exists(self.folder):
                os.makedirs(self.folder)
            self.copy_files_to(self.folder)
            result = self._cmd.run()
            self._state = DONE
            return result
        except Exception as exc:
            self.error = str(exc)
            self.state = FAILED
            raise
        finally:
            self.save()

    def copy_files_to(self, folder):
        """Copy the task files to the given folder.  The folder must exist already."""
        for file in self._files:
            file.to_disk(folder)


def task(cmd, args=None, folder: [str, Path] = ''):
    """Create a task"""
    folder = Path(folder).absolute()
    args = args or []

    return Task(commands.command(cmd, args), folder)


HISTORIAN_TYPES = (Task,)
