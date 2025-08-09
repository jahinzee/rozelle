# Rozelle: module for rich display functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle.exercise import (
    Exercise,
    FailConstraints,
    FailProgramError,
    FailOutput,
    FailAST,
    Result,
    Pass,
)

from pathlib import Path
from rich.console import Console, Group, ConsoleRenderable
from rich.syntax import Syntax
from rich.text import Text
from rich.columns import Columns
from rich.padding import Padding

import os

# region private

_BlankLine = Text()


def _full_clear_screen():
    """
    Clear the terminal screen including the scrollback.
    """
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def _get_result_text(result: Result) -> tuple[Text, Text, Group | None]:
    """
    Get the information necessary to display an Exercise' result output.

    Args:
        result (FailAST | FailConstraints | FailProgramError | FailOutput | None):
            The result from `(Exercise).run()`.

    Returns:
        tuple[Text, Text, Group | None]:
            `Text`:          a coloured badge (PASS/FAIL);
            `Text`:          a title message;
            `Group | None`:  a body object displayable with rich, or None if there's nothing to be
                             printed.

    """
    BADGE_PASS = Text("PASS:", style="bold green")
    BADGE_FAIL = Text("FAIL:", style="bold red")

    if type(result) is FailAST:
        return (
            BADGE_FAIL,
            Text("Your program cannot be examined due to a syntax error."),
            Group(Text(str(result.error))),
        )

    if type(result) is FailConstraints:
        critical = "critical" if result.critical else "these"
        descriptions = [Text(f"  · {d}") for d in result.failed_constraint_descriptions]
        return (
            BADGE_FAIL,
            Text(f"Your program failed to satisfy {critical} constraints."),
            Group(*descriptions),
        )

    if type(result) is FailProgramError:
        return (
            BADGE_FAIL,
            Text("Your program ran into an error."),
            Group(Text(result.program_stderr, style="grey")),
        )

    if type(result) is FailOutput:
        got = result.got.strip()
        return (
            BADGE_FAIL,
            Text("Your program does not have the expected output."),
            Group(Syntax(got, "text", line_numbers=True, background_color="default")),
        )

    if type(result) is Pass:
        return (
            BADGE_PASS,
            Text("Your program is correct!"),
            Group(Text(f"Execution time: {result.attempt_time_seconds}s")),
        )

    raise ValueError


def _display_result(console: Console, result: Result):
    """
    Display Exercise result information to the rich console.

    Args:
        console (Console): the rich Console object.
        result (FailConstraints | FailProgramError | FailOutput | None):
            The result from `(Exercise).run()`.
    """
    badge, message, body = _get_result_text(result)
    console.print(
        Padding(
            Group(
                Columns((badge, message)),
                # Ignoring types, ternary check disallowed None values to be unpacked
                *([] if body is None else [_BlankLine, body]),  # type: ignore
                _BlankLine,
                Text("Test will re-run on next file save.", style="bright_black"),
            ),
            (1, 3),
        )
    )


def _display_exercise(console: Console, exercise: Exercise):
    """
    Display Exercise information to the rich console.

    Args:
        console (Console): the rich Console object.
        exercise (Exercise): the exercise to display information about.
    """
    expected_output: list[ConsoleRenderable] = (
        []
        if exercise.hide_expected_output
        else [
            _BlankLine,
            Text("Expected output:", style="blue"),
            _BlankLine,
            Syntax(
                exercise.expected_output.strip(),
                "text",
                line_numbers=True,
                background_color="default",
            ),
        ]
    )
    constraints: list[ConsoleRenderable] = (
        []
        if exercise.hide_constraints
        else [
            _BlankLine,
            Text("Constraints:", style="blue"),
            _BlankLine,
            *[Text(f"  · {c.description}") for c in exercise.constraints],
        ]
    )
    console.print(
        Padding(
            Group(
                Text(exercise.message.strip()),
                *expected_output,
                *constraints,
            ),
            (1, 3),
        )
    )


# endregion
# region public


def display_run(
    exercise: Exercise,
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
        full_clear (bool, optional): if True, clears the scrollback. Defaults to False.
    """
    if full_clear:
        _full_clear_screen()

    console.clear()

    console.rule(f"Exercise: {exercise_name}", style="blue")
    _display_exercise(console, exercise)

    console.rule(f"Attempt: {python_file}", style="bright_black")
    with console.status("Evaluating code in sandbox...", spinner="bouncingBar"):
        result = exercise.run(python_file)

    _display_result(console, result)

    console.rule(style="bright_black")


# endregion
