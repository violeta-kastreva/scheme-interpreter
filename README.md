# Scheme Interpreter in Python

This is a simple Scheme interpreter implemented in Python. It supports the core syntax and evaluation rules of Scheme, including:

- Variable definitions and lambdas
- Conditionals and quoting
- Basic procedures and list operations
- Derived expressions like `let` and `cond`
- Support for `call/cc` using Python exceptions

The interpreter includes a tokenizer, parser, and evaluator. It also supports:

- Strings, booleans (`#t`, `#f`), and comments
- Quasiquote, unquote, and unquote-splicing
- Dotted list notation (as a stub)
- A basic REPL for interactive use

## Usage

To run the interpreter, use:

```bash
python3 scheme.py
