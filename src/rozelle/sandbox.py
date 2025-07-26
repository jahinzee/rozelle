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

import json
import secrets


def _mangle_name(name: str) -> str:
    """
    Returns a randomly mangled version of `name`, in the format of `"_XXXXXXXX__{name}"`, where `X`
    is a random hexadecimal digit (`0-9|a-d`).

    Mangling is non-deterministic - if you need to reuse a mangled identifier, save and reuse
    this function's output somewhere else.

    Args:
        name (str): The name to mangle.

    Returns:
        str: The mangled name
    """
    return f"_{secrets.token_hex(8)}__{name}"


async def run_python(code: str) -> tuple[str, bool]:
    """
    Run the Python file in a Pyodide sandbox, and return the stdout or stderr, depending on
    execution status, and a boolean indicating success.

    Args:
        python_file (str): The Python source to run.

    Returns:
        tuple[str, bool]: [contents of stdout], True,  if the code executed successfully
                          [contents of stderr], False, if the code did not execute successfully
    """

    # Prelude and epilogue snippets to be run before and after the code in `python_file`
    # respectively.
    #
    # PyodideSandbox by itself cannot stream out newlines properly so we're hijacking stdout to
    # point to a separate buffer, which we'll then stream out as a newline-separated JSON array
    # to be collected by the main code.
    #
    #  * Using __import__ instead of import (keyword) to avoid global modules leaking into the
    #    main code.
    #
    #  * Using GUID-based name mangling on the fake/real stdout variables to prevent them
    #    from being easily guessed.
    #
    #  * Using mangled start and end signals to filter out any unexpected stdin noise (e.g. from
    #    Pyodide import warnings we can safely ignore)
    #
    fake_stdout_ident = _mangle_name("stdout_fake")
    real_stdout_ident = _mangle_name("stdout_real")

    json_start_sentinel = f"***{_mangle_name('BEGIN_JSON')} ***"
    json_end_sentinel = f"***{_mangle_name('END_JSON')}***"

    PRELUDE = (
        "\n"
        f"{fake_stdout_ident} = __import__('io').StringIO()\n"
        f"{real_stdout_ident} = __import__('sys').stdout\n"
        f"__import__('sys').stdout = {fake_stdout_ident}\n"
        "\n"
    )

    EPILOGUE = (
        "\n"
        f"__import__('sys').stdout = {real_stdout_ident}\n"
        f'print("{json_start_sentinel}")\n'
        f"print(__import__('json').dumps({fake_stdout_ident}.getvalue().splitlines()))\n"
        f'print("{json_end_sentinel}")\n'
        "\n"
    )

    sandbox = PyodideSandbox(allow_net=False)
    result = await sandbox.execute(PRELUDE + code + EPILOGUE)

    if result.status != "success":
        # Program execution failed for some reason, could be a syntax error or runtime error.
        #
        return (result.stderr or "Could not get error information from Pyodide."), False

    # Parse stdout from JSON back into a proper newline'd string, extracting from between the
    # previously defined start and end signals.
    #
    parsed_result = "\n".join(
        json.loads(
            (result.stdout or f"{json_start_sentinel}[]{json_end_sentinel}")
            .split(json_start_sentinel, 1)[1]
            .split(json_end_sentinel, 1)[0]
        )
    )
    return parsed_result, True
