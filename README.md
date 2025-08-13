# Rozelle

A TUI-based Python code exercise runner.

- Runs attempts in a [Pyodide sandbox](https://github.com/langchain-ai/langchain-sandbox)
  for security and isolation.
- Custom exercises that check program output and [source code constraints](#constraints).
- Watches for file changes and re-runs on updates.
- Built-in exercise folder structure scaffolding for quickly getting started. 

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- [Deno](https://docs.deno.com/runtime/getting_started/installation/)
- [fzf](https://junegunn.github.io/fzf/) (optional, required for
  [`rozelle scaffold --select`](#menu-selection)).


## Exercises

See [Making your own exercises](/docs/exercises.md) for information on how to write exercises.

## Usage

### Standalone

Standalone mode (or `run` mode) is used for running a single exercise on a single attempt file.

```sh
rozelle run --attempt-file <attempt-file.py> -e <exercise-file.toml>
```

When an exercise is loaded, Rozelle will:

1. check if the attempt code is valid Python syntax,
2. check if the attempt code satisfies core security constraints,
  (see [exercise.py](/src/rozelle/exercise.py)'s `_CRITICAL_CONSTRAINTS`),
3. check if the attempt code satisfies the exercise's constraints,
4. execute the attempt code in a sandbox (and check if it runs successfully), and
5. compare the attempt's output to the expected output.

If any of these checks fail, Rozelle will output a message with details.

> [!NOTE]
> During attempt code execution, a `node_modules` folder (around 15 MB) will be generated in your
> working directory for the Pyodide sandbox.

A watcher checks for when the attempt file is changed, and re-runs the test when it does. The
watcher can be ended by exiting the program with `^C`.

By default, Rozelle will clear the screen without clearing the scrollback (as if you've pressed
`^L`). You can specify to always clear the scrollback with `-c/--full-clear`. This flag must go
immediately after `rozelle` before other commands and flags:

```sh
rozelle --full-clear # ... <other args go here>
```

### Scaffolds

You can also use a scaffold structure that will create a custom structure with an `exercises`
folder and an `attempt.py` file. This can be handy if you want to create a quick structure for
making your own exercises from.

You can create and work with scaffolded exercises with the `scaffold --init` subcommand.

```sh
rozelle scaffold --init
```

By default, the scaffolds will be created in/referenced from `./rozelle-scaffold/`. This can be
overriden with `-o/--scaffold-root <custom-directory>`.

#### Random selection

You can select a random test to run from your scaffold with the `--random` flag.

```sh
rozelle scaffold --random
```

#### Menu selection

Alternatively, you can select a test to run from an fuzzy-find menu with the `--select` flag.

> [!NOTE]
> This feature requires `fzf` to be installed.

```sh
rozelle scaffold --select
```

## License and Additional Notes

Rozelle is [open source software](https://opensource.org/osd), and is licensed under the
[Mozilla Public License, v. 2.0.](https://www.mozilla.org/en-US/MPL/2.0/). See
[LICENSE.txt](LICENSE.txt).

![Rozelle is a Brainmade project.](https://brainmade.org/88x31-dark.png)

Rozelle is a [Brainmade](https://brainmade.org/) project. None of the source code was written
with generative AI.