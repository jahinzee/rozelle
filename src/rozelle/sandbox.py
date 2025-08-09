# Rozelle: module for running Python code in a sandbox.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from langchain_sandbox import PyodideSandbox
from langchain_sandbox.pyodide import CodeExecutionResult
from functools import cache
from typing import Optional, NamedTuple
from io import StringIO
from pydantic import BaseModel, ValidationError

import ast
import json
import secrets
import asyncio

from importlib.resources import read_text
from . import sandbox_snippets as snippets

# region private

_SNIPPET_01 = read_text(snippets, "01_before_exercise_prerun.py.snippet")
_SNIPPET_03 = read_text(snippets, "03_after_exercise_prerun.py.snippet")
_SNIPPET_05 = read_text(snippets, "05_before_exercise_postrun.py.snippet")
_SNIPPET_07 = read_text(snippets, "07_after_exercise_postrun.py.snippet")

_SALT_SYSTEM = 0
_SALT_EXERCISE = 1
_SALT_ATTEMPT: None = None

_TIMEOUT_SECONDS = 20


@cache
def _mangle_identifier_if_possible(name: str, salt: int) -> str:
    MANGLE_PREFIX = "_RZ_MANGLE__"
    return (
        name.replace(
            MANGLE_PREFIX, f"_rozelle_mangled_{salt}_{secrets.token_hex(8)}__", count=1
        )
        if name.startswith(MANGLE_PREFIX)
        else name
    )


class _ExecutionStreamResults(BaseModel):
    stdout: list[str]
    tokens: set[str]
    attempt_time_seconds: float


class _SnippetAssemblyContext(NamedTuple):
    name: str
    text: str
    mangle_salt: int | None


class _NameMangler(ast.NodeTransformer):
    def __init__(self, salt):
        self.salt = salt

    def visit_Name(self, node: ast.Name):
        return ast.Name(
            id=_mangle_identifier_if_possible(node.id, self.salt), ctx=node.ctx
        )


def _prepare_python_source(code: str, mangle_salt: Optional[int] = None) -> str:
    code_ast = ast.parse(code)
    if mangle_salt is not None:
        code_ast = _NameMangler(mangle_salt).visit(code_ast)
    return ast.unparse(code_ast)


def _process_error_output(error: str | None) -> str:
    DEFAULT = "Could not get error information from Pyodide."
    if error is None:
        return DEFAULT
    lines = error.splitlines()
    if len(lines) == 0:
        return DEFAULT
    return lines[-1]


def _substring_between_two_substrings(input: str, left: str, right: str) -> str:
    return input.split(left, 1)[1].split(right, 1)[0]


async def _sandbox_execute_with_timeout(
    sandbox: PyodideSandbox, code: str
) -> Optional[CodeExecutionResult]:
    task = asyncio.create_task(sandbox.execute(code))

    complete, incomplete = await asyncio.wait([task], timeout=_TIMEOUT_SECONDS)

    if len(incomplete) != 0:
        task.cancel()
        return None

    result = await next(iter(complete))
    return result


# endregion
# region public


class ExecutionResult(NamedTuple):
    success: bool
    output: str
    tokens: Optional[set[str]]
    attempt_time_seconds: Optional[float]


def execute_attempt(
    attempt_code: str,
    exercise_prerun: Optional[str] = None,
    exercise_postrun: Optional[str] = None,
) -> ExecutionResult:
    """
    Run the Python file in a Pyodide sandbox, and return the stdout or stderr, depending on
    execution status, and a boolean indicating success.

    Args:
        attempt_code (str): The Python source to run from the attempt file.
        exercise_prerun (Optional[str], optional): Code specified by an exercise to run *before*
                                                   attempt code. Defaults to None.
        exercise_postrun (Optional[str], optional): Code specified by an exercise to run *after*
                                                    attempt code. Defaults to None.

    Returns:
        ExecutionResult: Contains:
            success (bool): Whether or not the code was run successfully.
            output (str): Either the extracted program stdout or stderr, depending on success.
            tokens (Optional[set[str]]): Any exercise tokens collected from exercise_postrun code.
    """

    # PyodideSandbox by itself cannot stream out newlines properly so we're hijacking stdout to
    # point to a separate buffer, which we'll then stream out as a newline-separated JSON array
    # to be collected by the main code.
    #
    #  * Using name mangling on identifiers to minimise risk of accidental usage/shadowing.
    #
    #  * Using start and end signals to filter out any unexpected stdin noise (e.g. from
    #    Pyodide import warnings we can safely ignore)
    #
    assembly = (
        _SnippetAssemblyContext(
            name="system, before exercise prerun",
            text=_SNIPPET_01,
            mangle_salt=_SALT_SYSTEM,
        ),
        _SnippetAssemblyContext(
            name="exercise prerun",
            text=exercise_prerun or "",
            mangle_salt=_SALT_EXERCISE,
        ),
        _SnippetAssemblyContext(
            name="system, after exercise prerun",
            text=_SNIPPET_03,
            mangle_salt=_SALT_SYSTEM,
        ),
        _SnippetAssemblyContext(
            name="attempt", text=attempt_code, mangle_salt=_SALT_ATTEMPT
        ),
        _SnippetAssemblyContext(
            name="system, before exercise postrun",
            text=_SNIPPET_05,
            mangle_salt=_SALT_SYSTEM,
        ),
        _SnippetAssemblyContext(
            name="exercise postrun",
            text=exercise_postrun or "",
            mangle_salt=_SALT_EXERCISE,
        ),
        _SnippetAssemblyContext(
            name="system, after exercise postrun",
            text=_SNIPPET_07,
            mangle_salt=_SALT_SYSTEM,
        ),
    )

    code = StringIO()
    for a in assembly:
        if len(a.text) == 0:
            continue
        try:
            prepared = _prepare_python_source(a.text, mangle_salt=a.mangle_salt)
        except SyntaxError as se:
            return ExecutionResult(
                success=False,
                output=(f"SyntaxError at <{a.name}> on line {se.lineno}:\n  {se.msg}"),
                tokens=None,
                attempt_time_seconds=None,
            )
        code.write(prepared + "\n\n")

    sandbox = PyodideSandbox(allow_net=False)
    sandbox_result = asyncio.run(
        _sandbox_execute_with_timeout(sandbox, code.getvalue())
    )

    if sandbox_result is None:
        return ExecutionResult(
            success=False,
            output="The attempt took too long to execute.",
            tokens=None,
            attempt_time_seconds=None,
        )

    if sandbox_result.status != "success":
        # Program execution failed for some reason, could be a syntax error or runtime error.
        #
        return ExecutionResult(
            success=False,
            output=_process_error_output(sandbox_result.stderr),
            tokens=None,
            attempt_time_seconds=None,
        )

    # Parse stdout from JSON back into a proper newline'd string, extracting from between the
    # previously defined start and end signals.
    #
    if sandbox_result.stdout is None:
        # Pyodide gave us a None stdout for some reason.
        #
        return ExecutionResult(
            success=False,
            output="Standard output could not be accessed.",
            tokens=None,
            attempt_time_seconds=None,
        )

    try:
        result = _ExecutionStreamResults.parse_obj(
            json.loads(
                _substring_between_two_substrings(
                    input=sandbox_result.stdout,
                    left="--- BEGIN JSON RESPONSE ---",
                    right="--- END JSON RESPONSE ---",
                )
            )
        )
        print(result)
    except json.JSONDecodeError as jsonde:
        return ExecutionResult(
            success=False,
            output=f"The sandbox failed to return a valid result ({jsonde.msg})",
            tokens=None,
            attempt_time_seconds=0.0,
        )
    except ValidationError as ve:
        return ExecutionResult(
            success=False,
            output=f"The sandbox failed to return a valid result ({ve.errors})",
            tokens=None,
            attempt_time_seconds=0.0,
        )

    return ExecutionResult(
        success=True,
        output="\n".join(result.stdout),
        tokens=result.tokens,
        attempt_time_seconds=result.attempt_time_seconds,
    )


# endregion
