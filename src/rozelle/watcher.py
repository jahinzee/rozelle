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
from watchdog import events as ev
from watchdog.observers import Observer

import time
import functools

# region private

_WATCH_DELAY_SECS = 0.1


class _FileChangeCallbackHandler(ev.FileSystemEventHandler):
    def __init__(self, path: Path, callback: Callable):
        self._callback = callback
        self._path = str(path)
        self._callback()

    def _file_missing(self, *, deleted: bool):
        print(f"Fatal error: file {'deleted' if deleted else 'moved'}.")
        exit(1)

    def _is_target_file(self, event: ev.FileModifiedEvent) -> bool:
        # See `watch_display_run`'s comments for more info.
        return event.src_path == str(self._path)

    def on_modified(self, event: ev.DirModifiedEvent | ev.FileModifiedEvent):
        if isinstance(event, ev.FileModifiedEvent) and self._is_target_file(event):
            self._callback()

    def on_moved(self, event: ev.DirMovedEvent | ev.FileMovedEvent):
        if isinstance(event, ev.FileModifiedEvent) and self._is_target_file(event):
            self._file_missing(deleted=False)

    def on_deleted(self, event: ev.FileDeletedEvent | ev.DirDeletedEvent):
        if isinstance(event, ev.FileModifiedEvent) and self._is_target_file(event):
            self._file_missing(deleted=True)


# endregion
# region public


def watch_display_run(
    exercise: Exercise,
    exercise_file: Path,
    python_file: Path,
    *,
    full_clear: bool = False,
):
    """
    Creates a watcher on the Python attempt file, and reruns and displays the exercise on file
    change.

    Args:
        exercise (Exercise): the exercise to run.
        python_file (Path): the attempt file to watch.
        full_clear (bool, optional): if True, clears the scrollback on rerun (see docs for
                                     Exercise.display_run). Defaults to False.
    """

    # We want to only run the callback on `python_file`'s events. watchdog can only monitor
    # directories, so we'll watch the file's parent, and add additional checks inside the monitor
    # class to only run the callback on file events.
    #
    # Passing in the file path directly to watchdog works fine on *NIX, but breaks on Windows.
    # (see <https://github.com/gorakhargosh/watchdog/issues/58>)
    #
    event = _FileChangeCallbackHandler(
        python_file,
        functools.partial(
            display_run,
            exercise,
            python_file,
            full_clear=full_clear,
        ),
    )

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
