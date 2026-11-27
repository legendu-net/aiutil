"""Format code and markdown cells in Jupyter/Lab notebooks."""

import shutil
import subprocess as sp
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path

import mdformat
import mdformat.plugins
import nbformat
from loguru import logger


def _default_extensions() -> set[str]:
    """Return default mdformat parser extensions available in the environment."""
    if "myst" in mdformat.plugins.PARSER_EXTENSIONS:
        return {"myst"}
    return set()


def _iter_notebook_cells(nb: object) -> list[dict]:
    """Extract cell dicts from an nbformat v4 or v3 notebook."""
    if not isinstance(nb, dict):
        raise TypeError("Notebook root must be a JSON object")
    if isinstance(cells := nb.get("cells"), list):
        return [c for c in cells if isinstance(c, dict)]
    if isinstance(worksheets := nb.get("worksheets"), list):
        return [
            c
            for ws in worksheets
            if isinstance(ws, dict) and isinstance(ws.get("cells"), list)
            for c in ws["cells"]
            if isinstance(c, dict)
        ]
    raise ValueError("Notebook contains neither 'cells' nor 'worksheets'")


def format_notebook_markdown(
    path: str | Path,
    extensions: set[str] | None = None,
) -> bool:
    """Format markdown cells (and their fenced code blocks) in a Jupyter notebook.

    Leaves code cells, raw cells, outputs, and execution counts untouched.

    :param path: Path to the ``.ipynb`` notebook file.
    :param extensions: Optional set of mdformat parser extension names.
        Defaults to ``{"myst"}`` when ``mdformat-myst`` is installed.
    :return: True if any markdown cell changed and the notebook was written back.
    """
    nb_path = Path(path)
    try:
        nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)
    except AttributeError as exc:
        raise ValueError(f"Invalid notebook structure in {nb_path}") from exc
    resolved_extensions = _default_extensions() if extensions is None else extensions
    changed = False
    for cell in _iter_notebook_cells(nb):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        if not isinstance(source, str) or not source.strip():
            continue
        formatted = mdformat.text(
            source,
            extensions=resolved_extensions,
            codeformatters=mdformat.plugins.CODEFORMATTERS,
        )
        if not source.endswith("\n"):
            formatted = formatted.removesuffix("\n")
        if formatted != source:
            cell["source"] = formatted
            changed = True
    if changed:
        nbformat.write(nb, nb_path)
    return changed


def format_notebook_code(path: str | Path) -> bool:
    """Format Python code cells in a Jupyter notebook using ``ruff format``.

    Leaves markdown cells and output cells untouched.

    :param path: Path to the ``.ipynb`` notebook file.
    :return: True if ``ruff format`` succeeded, False otherwise.
    """
    nb_path = Path(path)
    ruff_bin = shutil.which(
        "ruff", path=str(Path(sys.executable).parent)
    ) or shutil.which("ruff")
    cmd = (
        [ruff_bin, "format", "--", str(nb_path)]
        if ruff_bin is not None
        else [sys.executable, "-m", "ruff", "format", "--", str(nb_path)]
    )
    try:
        result = sp.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        logger.warning("Failed to invoke ruff for {}: {}", nb_path, exc)
        return False
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        logger.warning("Failed to format code cells in {}:\n{}", nb_path, detail)
        return False
    return True


def format_notebook(
    path: str | Path,
    *,
    format_code: bool = True,
    format_markdown: bool = True,
    extensions: set[str] | None = None,
) -> bool:
    """Format code and/or markdown cells in a single Jupyter notebook.

    :param path: Path to the ``.ipynb`` notebook file.
    :param format_code: Whether to format Python code cells with ``ruff format``.
    :param format_markdown: Whether to format markdown cells with ``mdformat``.
    :param extensions: Optional set of mdformat parser extension names.
    :return: True if all requested formatting steps succeeded, False otherwise.
    """
    nb_path = Path(path)
    if not nb_path.is_file():
        logger.warning("Notebook file does not exist: {}", nb_path)
        return False

    success = True
    if format_code and not format_notebook_code(nb_path):
        success = False

    if format_markdown:
        try:
            format_notebook_markdown(nb_path, extensions=extensions)
        except (
            OSError,
            ValueError,
            TypeError,
            SyntaxError,
            RuntimeError,
            AttributeError,
        ) as exc:
            logger.warning("Failed to format markdown cells in {}:\n{}", nb_path, exc)
            success = False

    return success


_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".ipynb_checkpoints",
        ".jj",
        ".venv",
        "node_modules",
        "venv",
    }
)


def _collect_notebooks(paths: Sequence[str | Path]) -> tuple[list[Path], list[Path]]:
    """Collect ``.ipynb`` files from file and directory paths.

    Skips any path inside ``.ipynb_checkpoints`` or VCS/env directories.
    Returns ``(notebooks, missing_or_invalid)``.
    """
    notebooks: dict[Path, None] = {}
    failed: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if path.suffix == ".ipynb":
                if ".ipynb_checkpoints" not in path.parts:
                    notebooks[path] = None
            else:
                logger.warning("Skipping non-notebook file: {}", path)
        elif path.is_dir():
            if ".ipynb_checkpoints" in path.parts:
                continue
            for root, dirs, files in path.walk():
                dirs[:] = sorted(d for d in dirs if d not in _IGNORED_DIRS)
                for name in sorted(files):
                    if name.endswith(".ipynb"):
                        notebooks[root / name] = None
        else:
            logger.warning("Path does not exist: {}", path)
            failed.append(path)
    return list(notebooks), failed


def format_notebooks(
    paths: Sequence[str | Path],
    *,
    format_code: bool = True,
    format_markdown: bool = True,
    extensions: set[str] | None = None,
) -> list[Path]:
    """Format notebooks under the given file or directory paths.

    Recursively searches directories for ``*.ipynb`` files while skipping
    ``.ipynb_checkpoints`` and VCS/virtual-env directories.

    :param paths: File and/or directory paths to format.
    :param format_code: Whether to format Python code cells with ``ruff format``.
    :param format_markdown: Whether to format markdown cells with ``mdformat``.
    :param extensions: Optional set of mdformat parser extension names.
    :return: List of paths that failed to format (empty on full success).
    """
    notebooks, failed = _collect_notebooks(paths)
    for nb_path in notebooks:
        if not format_notebook(
            nb_path,
            format_code=format_code,
            format_markdown=format_markdown,
            extensions=extensions,
        ):
            failed.append(nb_path)
    return failed


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments for ``format_notebook``."""
    parser = ArgumentParser(
        description="Format code and markdown cells in Jupyter notebooks.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Notebook files or directories to format (default: current directory).",
    )
    parser.add_argument(
        "--no-code",
        action="store_false",
        dest="format_code",
        help="Skip formatting code cells with ruff.",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_false",
        dest="format_markdown",
        help="Skip formatting markdown cells with mdformat.",
    )
    return parser.parse_args(args=argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for formatting Jupyter notebooks."""
    logger.enable("aiutil")
    args = parse_args(argv)
    failed = format_notebooks(
        args.paths,
        format_code=args.format_code,
        format_markdown=args.format_markdown,
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
