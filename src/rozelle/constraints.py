# Rozelle: module for exercise constraint data and functions.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

import ast

# region private


class _ConstraintType(Enum):
    Call = "call"
    Node = "node"
    PassToken = "pass-token"
    FailToken = "fail-token"


class _ConstraintLimit(BaseModel, frozen=True):
    minimum: Optional[int] = Field(None)
    maximum: Optional[int] = Field(None)

    def is_satisfied(self, count: int) -> bool:
        min_satisfied = self.minimum is None or count >= self.minimum
        max_satisfied = self.maximum is None or count <= self.maximum
        return min_satisfied and max_satisfied


# endregion
# region public


class Constraint(BaseModel, frozen=True):
    description: str
    on: _ConstraintType
    match: str
    limits: _ConstraintLimit = Field(default=_ConstraintLimit(minimum=None, maximum=None))


class _ConstraintScanner(ast.NodeVisitor):
    def __init__(self, constraints: list[Constraint]):
        self.constraint_counts = {c: 0 for c in constraints}

    def generic_visit(self, node):
        for c in self.constraint_counts.keys():
            if c.on == _ConstraintType.Node and type(node).__name__ == c.match:
                self.constraint_counts[c] += 1

            if (
                isinstance(node, ast.Call)
                and c.on == _ConstraintType.Call
                and node.func.id == c.match
            ):
                self.constraint_counts[c] += 1

        ast.NodeVisitor.generic_visit(self, node)


def DisallowedCall(name: str) -> Constraint:
    return Constraint(
        description=f"You cannot use the `{name}` function.",
        on=_ConstraintType.Call,
        match=name,
        limits=_ConstraintLimit(minimum=None, maximum=0),
    )


def DisallowedNode(name: str, description: str) -> Constraint:
    return Constraint(
        description=description,
        on=_ConstraintType.Node,
        match=name,
        limits=_ConstraintLimit(minimum=None, maximum=0),
    )


def check_syntax_constraints(python_ast: ast.AST, constraints: list[Constraint]) -> set[Constraint]:
    """
    Check if a given Python AST follows all the syntax constraints in `constraints`.

    Args:
        python_ast (ast.AST): the Python AST to examine.
        constraints (list[Constraint]): the list of constraints to check against.

    Returns:
        set[Constraint]: The list of constraints the code failed to satisfy, or an
                         empty list if the code satisfies all constraints.
    """

    scanner = _ConstraintScanner(constraints)
    scanner.visit(python_ast)

    return {c for c, count in scanner.constraint_counts.items() if not c.limits.is_satisfied(count)}


def check_token_constraints(tokens: set[str], constraints: list[Constraint]) -> set[Constraint]:
    """
    Check if a given set of execution tokens follows all the postrun constraints in `constraints`.

    Args:
        tokens (set[str]): the tokens collected after code execution.
        constraints (list[Constraint]): the list of constraints to check against.

    Returns:
        set[Constraint]: The list of constraints the code failed to satisfy, or an
                         empty list if the code satisfies all constraints.
    """
    # fmt: off
    return { c for c in constraints
             if c.on == _ConstraintType.PassToken and c.match not in tokens
           } | {
             c for c in constraints
             if c.on == _ConstraintType.FailToken and c.match in tokens }
    # fmt: on


# endregion
