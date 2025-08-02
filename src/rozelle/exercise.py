# Rozelle: module for exercise data and functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle.constraints import (
    Constraint,
    DisallowedFunctionConstraint,
    check_constraints,
)
from rozelle.sandbox import run_attempt_code

from typing import NamedTuple, Self
from pydantic import BaseModel, Field
from pathlib import Path

import re
import tomllib
import ast

_CRITICAL_CONSTRAINTS = [
    Constraint(
        description="You cannot import any other code.",
        ast_regex=re.compile(r"Import(?:From)?"),
        min_required=0,
        max_allowed=0,
    ),
    DisallowedFunctionConstraint("exec"),
    DisallowedFunctionConstraint("eval"),
    DisallowedFunctionConstraint("open"),
]


class FailAST(NamedTuple):
    """
    The program cannot be parsed into a Python AST.
    """

    error: SyntaxError


class FailConstraints(NamedTuple):
    """
    The program failed to pass the exercise, as the source code failed to pass the exercise's constraints.
    """

    critical: bool
    failed_constraint_descriptions: list[str]


class FailProgramError(NamedTuple):
    """
    The program failed to pass the exercise, as it returned an error.
    """

    program_stderr: str


class FailOutput(NamedTuple):
    """
    The program failed to pass the exercise, as its output does not match the expected output.
    """

    expected: str
    got: str


type Fail = FailAST | FailConstraints | FailProgramError | FailOutput
type Result = Fail | None


class Exercise(BaseModel):
    message: str
    expected_output: str
    constraints: list[Constraint] = Field([])
    hide_constraints: bool = Field(default=False)
    hide_expected_output: bool = Field(default=False)

    @classmethod
    def from_toml(cls, toml_file: Path) -> Self:
        """
        Constructs a valid Exercise from a TOML file.

        Args:
            toml_file (FileIO): An open .toml file to read from.

        Raises:
            OSError: if the file cannot be opened.
            tomllib.TOMLDecodeError: if the file is not valid TOML.
            pydantic.ValidationError: if the file is not a valid Exercise object.

        Returns:
            Self (Exercise): A valid Exercise object.
        """
        with open(toml_file, "rb") as f:
            return cls.model_validate(tomllib.load(f))

    def run(self, python_file: Path) -> Result:
        """
        Runs the exercise on the given Python file, and returns if it passed, or if and where it fails.

        Args:
            python_file (Path): the Python source code file.

        Returns:
            None:              if the program passes the exercise,
            FailConstraints:   if the source code failed to pass the exercise's constraints,
            FailProgramError:  if the program returned an error, or
            FailOutput:        its the program's output does not match the expected output
        """
        with open(python_file, "r") as f:
            code = f.read()

        # CHECK: The code must be valid Python (as in, can be parsed as AST)
        try:
            python_ast = ast.dump(ast.parse(code))
        except SyntaxError as se:
            return FailAST(se)

        # CHECK: The code must follow critical constraints, such as no imports and no uses of
        #        eval/exec.
        failed_criticals = check_constraints(python_ast, _CRITICAL_CONSTRAINTS)
        if len(failed_criticals) != 0:
            return FailConstraints(True, [c.description for c in failed_criticals])

        # CHECK: The code must follow all of the exercises's specified constraints.
        failed = check_constraints(python_ast, self.constraints)
        if len(failed) != 0:
            return FailConstraints(False, [c.description for c in failed])

        # CHECK: The program must execute successfully.
        result = run_attempt_code(code)
        if not result.success:
            return FailProgramError(program_stderr=result.output)

        # CHECK: The program's output must match the exercises's expected output.
        expected, got = self.expected_output.strip(), result.output.strip()
        if expected != got:
            return FailOutput(expected, got)

        return None
