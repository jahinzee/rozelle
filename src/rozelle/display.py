# Rozelle: module for rich display functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

import rozelle.exercise as ex

from pathlib import Path
from rich.console import Console, Group, RenderableType as Rt
from rich.syntax import Syntax
from rich.text import Text
from rich.columns import Columns
from rich.padding import Padding

import os

# region private


# Some reusable CLI rendering templates
# region templates

# Standard ruff formatting makes the layered parentheses very unruly, so we're temporarily disabling
# them -- enjoy the chaos!

# fmt: off

_BlankLine: Rt = \
    Text()


_BadgePass: Rt = \
    Text("PASS:", style="bold green")


_BadgeFail: Rt = \
    Text("FAIL:", style="bold red")


def _ListItem(text: str) -> Rt:
    return Text(f"  · {text}")

def _Padded(slot: Rt) -> Rt:
    return Padding(slot, (1, 3))


def _Exercise(e: ex.Exercise) -> Rt:
    return _Padded(
        Group(
            Text(e.message.strip()),
            *(() if e.hide_expected_output else (
                _BlankLine,
                Text(
                    f"Expected {'output' 
                        if e.check_expected_output_from == ex.ExerciseOutputSelection.Attempt 
                        else 'result'}:",
                    style="blue"),
                _BlankLine,
                Syntax(
                    e.expected_output.strip(),
                    "text",
                    line_numbers=True,
                    background_color="default"),
                *(() if e.check_expected_output_from == ex.ExerciseOutputSelection.Attempt else (
                    _BlankLine,
                    Text(
                        "Your code does not need to print any output.",
                        style="bright_black"))))),
            *(() if e.hide_constraints or len(e.constraints) == 0 else (
                _BlankLine,
                Text("Constraints:", style="blue"),
                _BlankLine,
                    *(_ListItem(c.description) for c in e.constraints)))))


def _ResultTemplate(badge: Rt, message: Rt, *body: Rt) -> Rt:
    return _Padded(
        Group(
            Columns((badge, message)),
            *(() if body is None else 
                (_BlankLine,
                 *body)), 
            _BlankLine,
            Text("Test will re-run on next file save.", style="bright_black")))


def _Result(result: ex.Result) -> Rt:
    match result:
        case ex.FailAST(error):
            return _ResultTemplate(
                _BadgeFail,
                Text("Your program cannot be examined due to a syntax error."),
                Text(str(error)))
           
        case ex.FailConstraints(critical, descriptions):
            return _ResultTemplate(
                _BadgeFail,
                Text((f"Your program failed to satisfy {"critical" if critical else "these"} "
                       "constraints.")),
                *(_ListItem(d) for d in descriptions))

        case ex.FailProgramError(stderr):
            return _ResultTemplate(
                _BadgeFail,
                Text("Your program ran into an error."),
                Text(stderr, style="grey"))

        case ex.FailOutput(_, got):
            return _ResultTemplate(
                _BadgeFail,
                Text("Your program does not have the expected output."),
                Syntax(
                    got.strip(),
                    "text",
                    line_numbers=True,
                    background_color="default"))

        case ex.Pass(time):
            return _ResultTemplate(
                _BadgePass,
                Text("Your program is correct!"),
                Text(f"Execution time: {time}s", style="grey"))

# fmt: on
# endregion


def _full_clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# endregion
# region public


def display_run(
    exercise: ex.Exercise,
    exercise_name: str,
    python_file: Path,
    console: Console,
    full_clear: bool = False,
):
    """
    Runs an exercise, and displays its description and results to the console

    Args:
        exercise (Exercise): the exercise to run.
        exercise_name (str): the filename the exercise was read from.
        python_file (Path): the attempt file to use.
        console (Console): the rich Console object.
        full_clear (bool, optional): if True, fully clears the scrollback. Defaults to False.
    """
    if full_clear:
        _full_clear_screen()

    console.clear()

    console.rule(f"Exercise: {exercise_name}", style="blue")
    console.print(_Exercise(exercise))

    console.rule(f"Attempt: {python_file}", style="bright_black")
    with console.status("Evaluating code in sandbox...", spinner="bouncingBar"):
        result = exercise.run(python_file)

    console.print(_Result(result))
    console.rule(style="bright_black")


# endregion
