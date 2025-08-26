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
from rozelle.sandbox import execute_attempt, ExecutionOutputs

from enum import Enum
from typing import NamedTuple, Self, Optional
from pydantic import BaseModel, Field
from pathlib import Path

import re
import tomllib
import ast

# region private

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

# endregion
# region public


class FailAST(NamedTuple):
    """
    The program cannot be parsed into a Python AST.
    """

    error: SyntaxError


class FailConstraints(NamedTuple):
    """
    The program failed to pass the exercise, as the source code failed to pass the exercise's
    constraints.
    """

    critical: bool
    failed_constraint_descriptions: list[str]


class FailProgramError(NamedTuple):
    """
    The program failed to pass the exercise, as it returned an error.
    """

    error: str


class FailOutput(NamedTuple):
    """
    The program failed to pass the exercise, as its output does not match the expected output.
    """

    expected: str
    got: str


class Pass(NamedTuple):
    attempt_time_seconds: float


type Fail = FailAST | FailConstraints | FailProgramError | FailOutput
type Result = Fail | Pass


class OutputSelection(Enum):
    Attempt = "attempt"
    Postrun = "postrun"
    NoCheck = "no-check"

    def get_output_stream(self, outputs: ExecutionOutputs) -> Optional[str]:
        match self:
            case OutputSelection.Attempt:
                return "\n".join(outputs.attempt).strip()
            case OutputSelection.Postrun:
                return "\n".join(outputs.postrun).strip()
            case OutputSelection.NoCheck:
                return None


class ExerciseDefinedCode(BaseModel):
    prerun: str = Field(default="")
    postrun: str = Field(default="")


class Exercise(BaseModel):
    message: str
    expected_output: str
    constraints: list[Constraint] = Field(default_factory=list)

    hide_constraints: bool = Field(default=False)
    hide_expected_output: bool = Field(default=False)

    code: ExerciseDefinedCode = Field(default_factory=ExerciseDefinedCode)

    check_expected_output_from: OutputSelection = Field(default=OutputSelection.Attempt)

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
        Runs the exercise on the given Python file, and returns if it passed, or if and where it
        fails.

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
            python_ast = ast.parse(code)
        except SyntaxError as se:
            se.filename = str(python_file)
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
        result = execute_attempt(
            code, exercise_prerun=self.code.prerun, exercise_postrun=self.code.postrun
        )
        if not result.success:
            return FailProgramError(error="\n".join(result.output.error))

        # CHECK: The program's output must match the exercises's expected output.
        expected = self.expected_output.strip()
        got = self.check_expected_output_from.get_output_stream(result.output)
        if got is not None and expected != got:
            return FailOutput(expected, got)

        return Pass(result.attempt_time_seconds or 0.0)


# endregion
