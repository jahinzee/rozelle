# Rozelle: main module for command-line interaction.
#
# Copyright (C) 2025 Jahin Z. <jahinzee@proton.me>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

__package__ = "rozelle"

from rozelle import scaffold, run
from rozelle.scaffold import SCAFFOLD_ROOT

from pathlib import Path
from argparse import ArgumentParser, Namespace

import sys


def parse_args() -> Namespace:
    """
    Parses command-line arguments. Exits the program for invalid arguments or if help text is
    to be displayed.

    Returns:
        Namespace: the parsed arguments.
    """
    parser = ArgumentParser(
        "rozelle", description="A TUI-based Python code exercise runner."
    )

    parser.add_argument(
        "-c",
        "--full-clear",
        help="fully clear the screen (including scrollback) on output refresh",
        action="store_true",
    )

    sp = parser.add_subparsers(help="subcommands", dest="subcommand")

    parser_run = sp.add_parser(
        "run", help="runs a given exercise on a given attempt file"
    )
    parser_run.add_argument(
        "-a",
        "--attempt-file",
        type=Path,
        required=True,
        help="the Python file to source attempt code from",
    )
    parser_run.add_argument(
        "-e",
        "--exercise-file",
        type=Path,
        required=True,
        help="the exercise TOML file to run",
    )

    parser_scaffold = sp.add_parser(
        "scaffold", help="run exercises from a predefined file structure"
    )
    parser_scaffold.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="initialise a scaffold folder structure with an example exercise and an attempts file",
    )
    parser_scaffold.add_argument(
        "-o",
        "--scaffold-root",
        type=Path,
        nargs="?",
        default=SCAFFOLD_ROOT,
        help="specifies a custom scaffold root directory",
    )
    parser_scaffold.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="select and run a random exercise from the scaffold with its attempts file",
    )
    parser_scaffold.add_argument(
        "-s",
        "--select",
        action="store_true",
        help="run an exercise selected from a menu with its attempt file (requires 'fzf' to be installed; overrides '-r/--random')",
    )

    return parser.parse_args()


def main():
    """
    Main function.
    """
    args = parse_args()
    if args.subcommand == "run":
        run.run(args.exercise_file, args.attempt_file, full_clear=args.full_clear)
    elif args.subcommand == "scaffold" and args.init:
        scaffold.init(args.scaffold_root)
    elif args.subcommand == "scaffold" and args.select:
        scaffold.run_fuzzy(args.scaffold_root, full_clear=args.full_clear)
    elif args.subcommand == "scaffold" and args.random:
        scaffold.run_random(args.scaffold_root, full_clear=args.full_clear)
    else:
        print(
            "Missing subcommand. Use '--help' for more information.",
            file=sys.stderr,
        )
        exit(1)


if __name__ == "__main__":
    main()
