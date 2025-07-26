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

A Rozelle exercise is written as a [TOML file](https://toml.io/en/), and contains:

- a main **message** that provides a description or some context for the exercise,
- the **expected output** the program should output, and
- any number of **constraints** to limit or require usage of specific Python syntax or builtins.

### Constraints

A constraint has:

- a human-readable **description**,
- a **regex** value to match for on the attempt code's
  [abstract syntax tree (AST)](https://docs.python.org/3/library/ast.html),
- a **maximum allowed** count for the regex to match (default: Infinity), and
- a **minimum required** count for the regex to match (default: 0).


### Notes on writing TOML exercises

- For the `message` and `expected_output` fields, any leading or trailing whitespace – including
  newlines – is trimmed at load time. This allows for some flexibility when writing TOML multiline
  strings.
  
  - This trimming is also applied to attempt code output for consistency in comparisons.

- When writing a regex for a constraint's `ast_regex`, you should be aware that TOML has its
  own set of `\` escape sequences that are different to Python's string and regex escapes
  (especially with parentheses).
  
  Invalid TOML escapes may result in incorrect or missed matches, or Rozelle being unable to
  parse the TOML file.
  
  - Consider using `'''TOML raw strings'''` to minimise escape sequence clashes.


An example exercise can be generated with [`rozelle scaffold`](#scaffold), and is also available
in the summary below:

<details>
<summary><strong>Example exercise TOML</strong></summary>

```toml
message = """
Can you write some code to say hello to all these people
with a for loop and only one print statement? 
"""

expected_output = """
Hello, Alice!
Hello, Bob!
Hello, Carol!
Hello, Dave!
"""

[[constraints]]
description = "You can only use the `print` function once."
ast_regex = '''func=Name\(id='print', ctx=Load\(\)\)'''
max_allowed = 1

[[constraints]]
description = "You must use atleast one `for` loop."
ast_regex = '''For'''
min_required = 1
```

</details>

<details>
<summary><strong>Sample Python code that passes the example exercice</strong></summary>

```py
for name in ["Alice", "Bob", "Carol", "Dave"]:
    print(f"Hello, {name}"!)
```

</details>

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