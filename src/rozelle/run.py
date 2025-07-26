# Rozelle: module for loading and running exercises from TOML files.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle.exercise import Exercise
from rozelle.watcher import watch_display_run

from tomllib import TOMLDecodeError
from pydantic import ValidationError
from pathlib import Path

import sys
import shutil


def run(exercise_file: Path, attempt_file: Path, full_clear: bool = False):
    """
    Loads an exercise from the given TOML file, and runs it in a watcher which also displays the
    output to the console.

    Args:
        exercise_file (Path): the exercise TOML file path.
        attempt_file (Path): the attempt Python file path,
        full_clear (bool, optional): if True, clears the scrollback. Defaults to False.
    """
    if shutil.which("deno") is None:
        print("Fatal error:", file=sys.stderr)
        print(
            "  - 'deno' is not available. Ensure it's installed and on your PATH.",
            file=sys.stderr,
        )
        exit(1)
    try:
        exercise = Exercise.from_toml(exercise_file)
    except OSError as oe:
        print(f"Error opening {exercise_file}:", file=sys.stderr)
        print(f"  - {oe}", file=sys.stderr)
        exit(1)
    except TOMLDecodeError as tde:
        print(f"Error parsing {exercise_file}:", file=sys.stderr)
        print(f"  - Invalid TOML syntax: {tde}", file=sys.stderr)
        exit(1)
    except ValidationError as ve:
        print(f"Error parsing {exercise_file}:", file=sys.stderr)
        for error in ve.errors():
            print(f"  - '{error['loc'][0]}': {error['msg']}", file=sys.stderr)
        exit(1)

    watch_display_run(exercise, exercise_file, attempt_file, full_clear=full_clear)
