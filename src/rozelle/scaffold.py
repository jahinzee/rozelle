# Rozelle: module for scaffold initialisation and usage functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle.run import run

from pathlib import Path
from pyfzf.pyfzf import FzfPrompt

import sys
import random
import shutil

SCAFFOLD_ROOT = Path("./rozelle-scaffold/")
_SCAFFOLD_EXERCISES = Path("exercises/")
_SCAFFOLD_ATTEMPT = Path("attempt.py")


def _get_file_tree(root: Path) -> dict[Path, str]:
    """
    Given a scaffold root, return the default scaffold file tree.

    Args:
        root (Path): the scaffold root.

    Returns:
        dict[Path, str]: a mapping of file paths to their contents.
    """
    return {
        Path(root / _SCAFFOLD_EXERCISES / "example.toml"): (
            "# rozelle-scaffold: example exercise.\n"
            "#\n"
            "# Any copyright is dedicated to the Public Domain.\n"
            "# https://creativecommons.org/publicdomain/zero/1.0/\n"
            "#\n"
            "\n"
            'message = """\n'
            "Can you write some Python code to say hello to Alice, Bob, Carol,\n"
            "and David with a for loop and only one print statement?\n"
            '"""\n'
            "\n"
            'expected_output = """\n'
            "Hello, Alice!\n"
            "Hello, Bob!\n"
            "Hello, Carol!\n"
            "Hello, Dave!\n"
            '"""\n'
            "\n"
            "[[constraints]]\n"
            'description = "You can only use the `print` function once."\n'
            r"ast_regex = '''func=Name\(id='print', ctx=Load\(\)\)'''"
            "\n"
            "max_allowed = 1\n"
            "\n"
            "[[constraints]]\n"
            'description = "You must use atleast one `for` loop."\n'
            r"ast_regex = '''For'''"
            "\n"
            "min_required = 1\n"
        ),
        Path(root / _SCAFFOLD_ATTEMPT): "",
    }


def _get_scaffold_exercises(scaffold_root: Path) -> list[Path]:
    """
    Given a scaffold root, return the paths of the exercises in it.

    Exits the program if no paths are found.

    Args:
        scaffold_root (Path): the scaffold root.

    Returns:
        list[Path]: a list of paths to TOML exercises in the scaffold.
    """
    exercise_path = Path(scaffold_root / _SCAFFOLD_EXERCISES)
    result = [fp for fp in exercise_path.glob("**/*.toml") if fp.is_file()]
    if len(result) == 0:
        print(f"No exercises found in '{exercise_path}.", file=sys.stderr)
        exit(0)
    return result


def init(scaffold_root: Path):
    """
    Initialise a scaffold in the given root.

    Exits the program if it's unsuccessful, or if the scaffold root already exists.

    Args:
        scaffold_root (Path): the scaffold root.
    """
    if scaffold_root.is_dir():
        print(f"Error creating scaffold at '{scaffold_root}':", file=sys.stderr)
        print("  - Folder already exists.", file=sys.stderr)
        exit(1)

    for path, content in _get_file_tree(scaffold_root).items():
        try:
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(content)
        except OSError as oe:
            print(f"Error creating file/folder '{path}':", file=sys.stderr)
            print(f"  - {oe}", file=sys.stderr)
            exit(1)


def run_random(scaffold_root: Path, full_clear: bool = False):
    """
    Selects and runs a random exercise from the scaffold root.

    Args:
        scaffold_root (Path): the scaffold root.
        full_clear (bool, optional): if True, clears the scrollback.. Defaults to False.
    """
    random_file = random.choice(_get_scaffold_exercises(scaffold_root))
    run(random_file, Path(scaffold_root / _SCAFFOLD_ATTEMPT), full_clear=full_clear)


def run_fuzzy(scaffold_root: Path, full_clear: bool = False):
    """
    Selects and runs a user-selected exercise from a fuzzy menu from the scaffold root.

    Exits if `fzf` cannot be found.

    Args:
        scaffold_root (Path): the scaffold root.
        full_clear (bool, optional): if True, clears the scrollback.. Defaults to False.
    """
    fzf_path = shutil.which("fzf")
    if fzf_path is None:
        print("Fatal error:", file=sys.stderr)
        print(
            "  - 'fzf' is not available. Ensure it's installed and on your PATH.",
            file=sys.stderr,
        )
        exit(1)

    fzf = FzfPrompt(fzf_path)
    selected_file = fzf.prompt(_get_scaffold_exercises(scaffold_root))
    if len(selected_file) == 0:
        print("No file selected.", file=sys.stderr)
        exit(1)

    attempt_file = Path(scaffold_root / _SCAFFOLD_ATTEMPT)
    run(selected_file[0], attempt_file, full_clear=full_clear)
