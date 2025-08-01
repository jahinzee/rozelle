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

import re
import ast


class Constraint(BaseModel):
    description: str
    ast_regex: re.Pattern
    min_required: Optional[int] = Field(None)
    max_allowed: Optional[int] = Field(None)

    def check(self, python_ast: ast.AST | str) -> bool:
        """
        Returns true if the provided Python code (AST) satisfies
        this constraint.

        Args:
            python_ast (ast.AST): the AST of the code to check.

        Throws:
            SyntaxError: the Python source has invalid syntax.

        Returns:
            bool: True if the code passes the constraint.
        """
        if type(python_ast) is ast.AST:
            python_ast = ast.dump(python_ast)

        matches = self.ast_regex.findall(python_ast)
        count = len(matches)

        return not any(
            (
                self.min_required is not None and count < self.min_required,
                self.max_allowed is not None and count > self.max_allowed,
            )
        )


def DisallowedFunctionConstraint(name: str) -> Constraint:
    return Constraint(
        description=f"You cannot use the `{name}` function.",
        ast_regex=re.compile(r"func=Name\(id='" + name + r"', ctx=Load\(\)\)"),
        min_required=0,
        max_allowed=0,
    )


def check_constraints(
    python_ast: str, constrainsts: list[Constraint]
) -> list[Constraint]:
    """
    Check if a given Python AST follows the specified list of constraints.

    Args:
        python_ast (str): the Python AST to examine.
        constrainsts (list[Constraint]): the list of constraints to check against.

    Returns:
        list[Constraint]: The list of constraints the code failed to satisfy, or an
                          empty list if the code satisfies all constrainsts.
    """

    return [c for c in constrainsts if not c.check(python_ast)]
