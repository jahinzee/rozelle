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

from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, DirModifiedEvent
from watchdog.observers import Observer
from rich.console import Console

import time

_WATCH_DELAY_SECS = 0.1


class ExerciseReloadEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        exercise: Exercise,
        exercise_path: Path,
        python_file: Path,
        console: Console,
        full_clear: bool = False,
    ):
        self.exercise = exercise
        self.exercise_path = exercise_path
        self.python_file = python_file
        self.console = console
        self.full_clear = full_clear
        self._callback()

    def _callback(self):
        display_run(
            self.exercise,
            str(self.exercise_path),
            self.python_file,
            self.console,
            full_clear=self.full_clear,
        )

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        self._callback()

    def on_moved(self, _e):
        print("File moved, aborting program...")
        exit(1)

    def on_deleted(self, _e):
        print("File deleted, aborting program...")
        exit(1)


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
    event = ExerciseReloadEventHandler(
        exercise, exercise_file, python_file, console, full_clear
    )

    observer = Observer()
    observer.schedule(event, str(python_file), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(_WATCH_DELAY_SECS)
    except KeyboardInterrupt:
        observer.stop()
        console.clear()
    observer.join()
