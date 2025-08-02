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
from importlib import resources as import_res
from functools import cache
from typing import Optional, NamedTuple

import ast
import json
import secrets
import asyncio

from . import sandbox_snippets

_SNIPPETS = import_res.files(sandbox_snippets)
_SNIPPETS_PREAMBLE = import_res.read_text(sandbox_snippets, "preamble.py.snippet")
_SNIPPETS_INTERLUDE = import_res.read_text(sandbox_snippets, "interlude.py.snippet")
_SNIPPETS_EPILOGUE = import_res.read_text(sandbox_snippets, "epilogue.py.snippet")

_MANGLE_PREFIX = "_RZ_MANGLE__"


@cache
def _mangle_identifier_if_possible(name: str, hash: int = 0) -> str:
    return (
        name.replace(
            _MANGLE_PREFIX, f"_rozelle_mangled_{hash}_{secrets.token_hex(8)}__", count=1
        )
        if name.startswith(_MANGLE_PREFIX)
        else name
    )


class _NameMangler(ast.NodeTransformer):
    def __init__(self, hash):
        self.hash = hash

    def visit_Name(self, node: ast.Name):
        return ast.Name(
            id=_mangle_identifier_if_possible(node.id, self.hash), ctx=node.ctx
        )


def _prepare_python_source(code: str, mangle: Optional[int] = None) -> str:
    code_ast = ast.parse(code)
    if mangle is not None:
        code_ast = _NameMangler(mangle).visit(code_ast)
    return ast.unparse(code_ast)


def _substring_between_two_substrings(input: str, left: str, right: str) -> str:
    return input.split(left, 1)[1].split(right, 1)[0]


class ExecutionResult(NamedTuple):
    success: bool
    output: str
    tokens: Optional[set[str]]


def run_attempt_code(
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

    # Prelude and epilogue snippets to be run before and after the code in `python_file`
    # respectively.
    #
    # PyodideSandbox by itself cannot stream out newlines properly so we're hijacking stdout to
    # point to a separate buffer, which we'll then stream out as a newline-separated JSON array
    # to be collected by the main code.
    #
    #  * Using name mangling on identifiers to minimise risk of accidental usage/shadowing.
    #
    #  * Using start and end signals to filter out any unexpected stdin noise (e.g. from
    #    Pyodide import warnings we can safely ignore)
    #
    # See also:
    #   src/rozelle/sandbox_snippets/preamble.py.snippet
    #   src/rozelle/sandbox_snippets/interlude.py.snippet
    #   src/rozelle/sandbox_snippets/epilogue.py.snippet
    #
    preamble = _prepare_python_source(_SNIPPETS_PREAMBLE, mangle=0)
    interlude = _prepare_python_source(_SNIPPETS_INTERLUDE, mangle=0)
    epilogue = _prepare_python_source(_SNIPPETS_EPILOGUE, mangle=0)
    code = preamble + "\n" + attempt_code + "\n" + interlude + "\n" + epilogue

    sandbox = PyodideSandbox(allow_net=False)
    result = asyncio.run(sandbox.execute(code))

    if result.status != "success":
        # Program execution failed for some reason, could be a syntax error or runtime error.
        #
        return ExecutionResult(
            success=False,
            output=result.stderr or "Could not get error information from Pyodide.",
            tokens=None,
        )

    # Parse stdout from JSON back into a proper newline'd string, extracting from between the
    # previously defined start and end signals.
    #
    if result.stdout is None:
        # Pyodide gave us a None stdout for some reason.
        #
        return ExecutionResult(
            success=False,
            output="Standard output could not be accessed.",
            tokens=None,
        )

    try:
        output = json.loads(
            _substring_between_two_substrings(
                input=result.stdout,
                left="--- BEGIN JSON RESPONSE ---",
                right="--- END JSON RESPONSE ---",
            )
        )
        stdout, tokens = "\n".join(output["stdout"]), set(output["tokens"])
    except (IndexError, KeyError, json.JSONDecodeError):
        # One of these problems have occured:
        #   * IndexError:       incorrect stdout extraction
        #   * KeyError:         missing JSON field
        #   * JSONDecodeError:  invalid JSON data
        #
        return ExecutionResult(
            success=False,
            output="Standard output contains malformed or unexpected results.",
            tokens=None,
        )

    return ExecutionResult(success=True, output=stdout, tokens=tokens)
