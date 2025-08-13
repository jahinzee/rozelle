# Rozelle: Making your own exercises

A Rozelle exercise is written as a [TOML file](https://toml.io/en/), and contains:

- a main **message** that provides a description or some context for the exercise,
- the **expected output** the program should output,
- any number of **constraints** to limit or require usage of specific Python syntax or builtins, and
- optionally, some arbitrary Python **code** that will execute in the attempt sandbox (before or
  after the attempt code)


```toml
message = """
Can you write some code to say hello to all these people \
with a for loop and only one print statement? 
"""

expected_output = """
Hello, Alice!
Hello, Bob!
Hello, Carol!
Hello, Dave!
"""

# …
```

<details>
<summary><strong>Sample Python code that passes the example exercise</strong></summary>

```py
for name in ["Alice", "Bob", "Carol", "Dave"]:
    print(f"Hello, {name}!")
```

</details>

## Writing constraints

A constraint has:

- a human-readable **description**,
- a **regex** value to match for on the attempt code's
  [abstract syntax tree (AST)](https://docs.python.org/3/library/ast.html),
- a **maximum allowed** count for the regex to match (default: Infinity), and
- a **minimum required** count for the regex to match (default: 0).

```toml
[[constraints]]
description = "You can only use the `print` function once."
ast_regex = '''func=Name\(id='print', ctx=Load\(\)\)'''
max_allowed = 1
```

## Writing prerun and postrun code

Rozelle exercises support running arbitrary code inside the execution sandbox, before the attempt
code (**prerun**), and/or after attempt code (**postrun**).

Prerun and postrun code can be useful for dynamic attempt result verification, and for exposing
variables, functions and imported modules to attempts.

You can define prerun and postrun code with the `[code]` TOML block and the `prerun` and `postrun`
keys:

```toml
[code]
prerun = """
magic_variable = 42
"""

postrun = """
print(magic_variable)
"""
```

### Understanding the sandbox

The Python sandbox where attempt code is tested has seven "stages":

- The **attempt** stage, where attempt code runs and evaluates,
- The **prerun** and **postrun** stages, which run code defined in the exercise file before and
  after the attempt code, respectively, and
- **four system** stages, which handle startup, cleanup, and transitions between the three stages
  mentioned earlier.

```
system₁ → prerun → system₃ → attempt → system₅ → postrun → system₇
           ~~~~~~                                     ~~~~~~~
```

As an exercise writer, you only need to worry about what happens in the **prerun** and **postrun**
stages.

Variables and functions are shared between prerun and postrun, and prerun variables are also exposed
to attempt code (unless they are [mangled](#variable-mangling)).

### Variable mangling

The Rozelle sandbox supports runtime *mangling* of variables. You can tell Rozelle to mangle a
variable by prefixing its name with `_RM__` (one underscore at the start, two at the end).

If a variable is set to be mangled, its name will be changed to a unique name that can't be easily
guessed by system-stage or attempt-stage code.

So this code defined in the exercise:

```toml
prerun = """
_RM__magic_variable = 42
"""

postrun = """
print(_RM__magic_variable)
"""
```

…will become the following at runtime:

```py
_rozelle_mangled_1_deadbeef__magic_variable = 42

# …attempt code…

print(_rozelle_mangled_1_deadbeef__magic_variable)  # …or something along these lines, `deadbeef`
                                                    # represents a random 8-digit hex value.

```

> [!WARNING]
> Function declarations are not mangled, even if the function name is prefixed with `_RM__`.

Mangled names are useful, especially in exercise prerun code, to store private data that attempt
code should not directly access.

If you want to expose some variable to attempt code from prerun, simply do not mangle it.

Mangled variables are also shared between prerun and postrun code - if a variable `_RM__foo` is
defined in prerun, that same variable will also be available in postrun as `_RM__foo`.

### Capturing postrun output

The three main stages (**prerun**, **attempt**, and **postrun**) have separate *standard output*
buffers - i.e. if they use `print()`, they will all be written to different outputs.

By default, `expected_output` is matched against printed output from the attempt stage. You can
instead match against the postrun output with the `check_expected_output_from` key (at top-level,
not in `[code]` or `[constraints]`).

```toml 
check_expected_output_from = "postrun"
```

With this set, you can now control program output with postrun code. This is useful if your
exercise requires a function to be implemented, and you want to test the function results, instead
of whatever the attempt code prints.

Alternatively, you can set `check_expected_output_from = "no-check"` to completely disable output
checks - the code will only need to pass any static constraints.

## Additional flags

You can also define additional settings to control how the exercise is displayed. These keys are
top-level.

### `hide_expected_output`

If `true`, hides the expected output from the user (default: `false`)

### `hide_constraints`

If `true`, hides the constraints from the user (default: `false`)