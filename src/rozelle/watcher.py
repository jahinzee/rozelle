# Rozelle: module for attempt file watcher functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle.exercise import Exercise
from rozelle.display import display_run

from typing import Callable
from pathlib import Path
from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    DirModifiedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
    DirMovedEvent,
    FileMovedEvent,
)

from watchdog.observers import Observer
from rich.console import Console

import time

# region private

_WATCH_DELAY_SECS = 0.1


class _FileChangeCallbackHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable, path: Path):
        self._callback = callback
        self._path = str(path)
        self._callback()

    def _file_missing(self, deleted: bool):
        print(f"Fatal error: file {'deleted' if deleted else 'moved'}.")
        exit(1)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        # See `watch_display_run`'s comments for more info.
        if type(event) is FileModifiedEvent and event.src_path == str(self._path):
            self._callback()

    def on_moved(self, event: DirMovedEvent | FileMovedEvent):
        # See `watch_display_run`'s comments for more info.
        if type(event) is FileModifiedEvent and event.src_path == str(self._path):
            self._file_missing(False)

    def on_deleted(self, event: FileDeletedEvent | DirDeletedEvent):
        # See `watch_display_run`'s comments for more info.
        if type(event) is FileModifiedEvent and event.src_path == str(self._path):
            self._file_missing(True)


# endregion
# region public


def watch_display_run(
    exercise: Exercise, exercise_file: Path, python_file: Path, full_clear: bool = False
):
    """
    Creates a watcher on the Python attempt file, and reruns and displays the exercise on file
    change.

    Args:
        exercise (Exercise): the exercise to run.
        exercise_name (str): the filename the exercise was read from.
        python_file (Path): the attempt file to watch.
        full_clear (bool, optional): if True, clears the scrollback. Defaults to False.
    """
    console = Console()
    callback = lambda: display_run(  # noqa: E731
        exercise, str(exercise_file), python_file, console, full_clear=full_clear
    )

    # We want to only run the callback on `python_file`'s events. watchdog can only monitor
    # directories, so we'll watch the file's parent, and add additional checks inside the monitor
    # class to only run the callback on file events.
    #
    # Passing in the file path directly to watchdog works fine on *NIX, but breaks on Windows.
    # (see <https://github.com/gorakhargosh/watchdog/issues/58>)
    #
    event = _FileChangeCallbackHandler(callback, python_file)

    observer = Observer()

    # Using the parent
    observer.schedule(event, str(python_file.parent), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(_WATCH_DELAY_SECS)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# endregion
