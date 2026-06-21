# AI Agent Context: aiutil

This project is a comprehensive Python utility package designed for data scientists and AI/ML engineers. 
It provides a wide range of helper functions and command-line tools 
to streamline common tasks in data processing, filesystem management, Hadoop/Spark interaction, and more.

## Project Overview

- **Core Purpose:** To provide "misc utils for AI/ML", 
    including enhancements to Python's built-in functionalities and specialized tools for data science workflows.
- **Main Technologies:**
  - **Language:** Python (>=3.12, supports up to 3.14).
  - **Environment Management:** [uv](https://github.com/astral-sh/uv) is used for dependency management and task execution.
  - **Build System:** [hatchling](https://hatch.pypa.io/).
  - **Key Libraries:** Pandas, NumPy, Loguru (logging), Tqdm (progress bars), Pytest, Ruff (linting/formatting).
- **Architecture:** The project is organized as a flat package `aiutil` with multiple submodules:
  - `aiutil.dataframe`: Pandas DataFrame enhancements.
  - `aiutil.filesystem`: Advanced filesystem and text file manipulation.
  - `aiutil.hadoop`: Spark log analysis, HDFS wrappers, and Kerberos auth.
  - `aiutil.notebook`: Jupyter notebook search and utility tools.
  - `aiutil.cv`: Image processing tools supplementing OpenCV.
  - `aiutil.pyscript`: Tools for managing and creating Python scripts.

## Building and Running

### Development Environment
Use `uv` to sync the environment:
```bash
uv sync --all-extras
```

### Testing
Run the full test suite using `pytest` via `uv`:
```bash
uv run pytest tests
```

### Linting and Formatting
The project uses `ruff` for linting and formatting:
```bash
uv run ruff check .
uv run ruff format .
```

### Executable Scripts
Several scripts are exposed as entry points (defined in `pyproject.toml`):
- `snb`: Search content in Jupyter notebooks.
- `logf`: Analyze Spark application logs for root cause analysis.
- `pyspark_submit`: Simplified Spark job submission.
- `pykinit`: Kerberos authentication helper.
- `match_memory`: Memory consumption/querying tool.
- `add_pyscript`: Create a new Python script from a template.

You can run these without local installation using `uvx`:
```bash
uvx --from aiutil snb -h
```

## Development Conventions

- **Type Hinting:** Modern Python type hints (e.g., `str | Path`, `pd.DataFrame | pd.Series`) are strictly used throughout the codebase.
- **Path Handling:** Prefer `pathlib.Path` over `os.path` for all filesystem operations.
- **Logging:** Use `loguru.logger` for all logging needs.
- **Docstrings:** Follow standard Python docstring conventions for all public functions and classes.
- **File Structure:** 
  - Submodules should be placed within the `aiutil/` directory.
  - Corresponding tests should be placed in the `tests/` directory, mirroring the package structure where possible.
- **Tooling:** Always check for existing utilities in `aiutil/utils.py` 
    or relevant submodules before implementing new helper functions.
