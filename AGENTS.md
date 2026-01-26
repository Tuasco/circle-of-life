# AGENTS.md

This file documents agents, commands, and code style guidelines for the project. It serves as a guide for agentic coding agents operating in this repository.

## Agents

- General: For general-purpose tasks.
- Explore: For exploring codebases.

## Commands

### Build Commands
- **Compile Python Files**: `python -m py_compile src/*.py` - Checks syntax without running.
- **Run Main Script**: `python src/display.py` - Executes the main display process (assumes venv activated).
- **Full Build (if applicable)**: No dedicated build tool (e.g., no Makefile); use above for Python compilation.

### Lint and Format Commands
- **Format Code**: `black .` - Applies Black formatter to all Python files (installed in venv).
- **Check Formatting**: `black --check .` - Verifies if code is formatted without changes.
- **Linting**: No dedicated linter configured (e.g., no flake8); rely on Black and manual review.
- **Type Checking**: `mypy src/` - Runs MyPy for type hints (installed in venv).
- **All Checks**: Run `black --check . && python -m py_compile src/*.py && mypy src/` for comprehensive validation.

### Test Commands
- **Run All Tests**: `pytest` - Executes all tests (install with `pip install pytest` if needed).
- **Run Tests in Directory**: `pytest tests/` - Runs tests in the tests/ directory.
- **Run Single Test**: `pytest tests/test_file.py::test_function_name` - Executes a specific test function.
- **Run Tests with Coverage**: `pytest --cov=src` - Runs tests with coverage report (install pytest-cov first).
- **Verbose Output**: `pytest -v` - Detailed test output.
- **Setup Tests**: Create `tests/` directory with files like `test_display.py` with functions prefixed with `test_`.

### Environment Setup
- **Activate Venv**: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows).
- **Current Dependencies** (in venv): black, mypy_extensions, posix_ipc (for POSIX message queues).
- **Add Dependency**: `pip install package_name` (update requirements.txt if one is created).

### Other Useful Commands
- **Git Status**: `git status` - Check repo state.
- **Commit Changes**: `git add . && git commit -m "message"` - Stage and commit.
- **Push**: `git push` - Push to remote.
- **Pull**: `git pull` - Pull latest changes.

## Code Style Guidelines

### General Principles
- Follow PEP 8 (Python Enhancement Proposal 8) for overall style.
- Use Black for automatic formatting (line length 88 chars, double quotes for strings).
- Prioritize readability, maintainability, and consistency.
- Write code for Python 3.8+ (tested with Python 3.14).
- No external rules from Cursor (.cursor/rules/ or .cursorrules not found) or Copilot (.github/copilot-instructions.md not found).

### Imports
- Use absolute imports: `from src.module import function` instead of relative.
- Group imports: standard library first, then third-party, then local.
- Avoid wildcard imports (`from module import *`).
- Sort imports alphabetically within groups.
- Example:
  ```
  import os
  import sys

  from typing import List, Optional

  from src.display import Parser
  ```

### Formatting
- Use Black: Run `black .` before commits.
- Indent with 4 spaces.
- Line length: 88 characters (Black default).
- Use double quotes for strings: `"string"` not `'string'`.
- Trailing commas in multi-line structures.
- Blank lines: 2 between top-level functions/classes, 1 within.

### Types and Type Hints
- Use type hints for all function parameters and return values.
- For complex types, import from `typing`: `List`, `Dict`, `Optional`, etc.
- Use `Union` for multiple types.
- Example: `def parse_command(command: str) -> Optional[ParsedCommand]:`
- Run `mypy` to check types.

### Naming Conventions
- **Functions/Variables**: snake_case (e.g., `parse_command`, `worker_index`).
- **Classes**: PascalCase (e.g., `CommandParser`).
- **Constants**: UPPER_SNAKE_CASE (e.g., `ACTION_TOKENS`).
- **Private Members**: Prefix with `_` (e.g., `_private_var`); use `__` for name mangling if needed (e.g., `__execute_command_no_op__`).
- **Modules**: lowercase with underscores (e.g., `display_renderer.py`).
- Avoid single-letter names except in loops (e.g., `for i in range(n)`).

### Functions and Classes
- Functions: Keep under 50 lines; extract if longer.
- Classes: Use dataclasses for simple data holders (from `dataclasses` import `dataclass`).
- Methods: First param `self` for instance methods.
- Docstrings: Use triple quotes for all public functions/classes.
  - Format: Brief description, then params and returns.
  - Example:
    ```
    def parse_command(command: str) -> Optional[ParsedCommand]:
        """Parse a command string into a ParsedCommand object.

        Args:
            command: The input command string.

        Returns:
            ParsedCommand if valid, None otherwise.
        """
    ```

### Error Handling
- Use exceptions for errors: Raise `ValueError`, `RuntimeError`, etc.
- Avoid bare `except:`; catch specific exceptions.
- Use `try/except/else/finally` appropriately.
- Log errors with `logging` module if needed (import `logging`).
- Example:
  ```
  try:
      result = risky_operation()
  except ValueError as e:
      logging.error(f"Invalid value: {e}")
      return None
  ```

### Best Practices
- **Security**: Avoid eval/exec; sanitize inputs (e.g., for socket data).
- **Performance**: Use lists/dicts efficiently; avoid global state.
- **Testing**: Write unit tests for functions; use pytest.
- **Concurrency**: For threading (e.g., in display), use `threading.Lock` if shared state.
- **Comments**: Use sparingly; prefer descriptive names. No inline comments unless complex logic.
- **Magic Numbers**: Define as constants.
- **File Structure**: Keep modules under 500 lines; split into packages (e.g., `src/display/`).
- **Commits**: Use imperative mood (e.g., "Add parser function"); reference issues if applicable.

### Project-Specific Notes
- **Architecture Overview**: Simulation of prey, predators, and grass. Display (parent process) spawns Env (state manager) and handles interpreter, display, and threading for blocking ops (socket for joining prey/predators, POSIX MQ to Env, signals, timer). Env sends full state snapshots via POSIX MQ. Prey/predators join via socket (role → ID response), then communicate with Env via shared memory.
- **Communication**: POSIX message queues (via `message_queue.py`) for Display-Env, shared memory for prey/predator-Env, sockets only for joining.
- **Threading in Display**: At least threads for socket listener, MQ listener, signal handler, and timer.
- **Threading in Env**: At least 4 threads: MQ listener (from Display), timer/signal, socket for joining, main loop (grass management).
- **Message Queues**: Use `MessageQueue` class (`src/message_queue.py`) which wraps POSIX IPC message queues with Queue-like interface.
- **Individual Processes**: Launched by parser via `Process(target=individual_main, args=(IndividualType.PREY/PREDATOR,))`. Support `verbose=True` flag for debugging.
- **Based on `display.py`**: Use `__` for internal functions; avoid tuple assignments (use lists).
- Simulation Context: Handle multiprocessing safely (MQ for inter-process, shared mem carefully); no locks in Env except for shared memory.

### Enforcement
- Run `black . && python -m py_compile src/*.py && mypy src/` before PRs.
- Use pre-commit hooks if set up (none currently).
- Review: Ensure style in code reviews.

This document is ~150 lines and should be updated as the project evolves.