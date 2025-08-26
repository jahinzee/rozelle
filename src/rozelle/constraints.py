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


class ConstraintType(Enum):
    Call = "call"
    Node = "node"


class ConstraintLimit(BaseModel, frozen=True):
    minimum: Optional[int] = Field(None)
    maximum: Optional[int] = Field(None)

    def is_satisfied(self, count: int) -> bool:
        min_satisfied = self.minimum is None or count >= self.minimum
        max_satisfied = self.maximum is None or count <= self.maximum
        return min_satisfied and max_satisfied


class Constraint(BaseModel, frozen=True):
    description: str
    on: ConstraintType
    match: str
    limits: ConstraintLimit = Field(default=ConstraintLimit(minimum=None, maximum=None))


def DisallowedCall(name: str) -> Constraint:
    return Constraint(
        description=f"You cannot use the `{name}` function.",
        on=ConstraintType.Call,
        match=name,
        limits=ConstraintLimit(minimum=None, maximum=0),
    )


def DisallowedNode(name: str, description: str) -> Constraint:
    return Constraint(
        description=description,
        on=ConstraintType.Node,
        match=name,
        limits=ConstraintLimit(minimum=None, maximum=0),
    )


class ConstraintScanner(ast.NodeVisitor):
    def __init__(self, constraints: list[Constraint]):
        self.constraint_counts = {c: 0 for c in constraints}

    def generic_visit(self, node):
        for c in self.constraint_counts.keys():
            if c.on == ConstraintType.Node and type(node).__name__ == c.match:
                self.constraint_counts[c] += 1

            if (
                isinstance(node, ast.Call)
                and c.on == ConstraintType.Call
                and node.func.id == c.match
            ):
                self.constraint_counts[c] += 1

        ast.NodeVisitor.generic_visit(self, node)


def check_constraints(
    python_ast: ast.AST, constraints: list[Constraint]
) -> set[Constraint]:
    """
    Check if a given Python AST follows the specified list of constraints.

    Args:
        python_ast (ast.AST): the Python AST to examine.
        constraints (list[Constraint]): the list of constraints to check against.

    Returns:
        list[Constraint]: The list of constraints the code failed to satisfy, or an
                        empty list if the code satisfies all constraints.
    """

    scanner = ConstraintScanner(constraints)
    scanner.visit(python_ast)

    return {
        c
        for c, count in scanner.constraint_counts.items()
        if not c.limits.is_satisfied(count)
    }
