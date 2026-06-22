import argparse
import os
import re
import subprocess as sp
from collections.abc import Iterable, Sequence
from pathlib import Path


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(
        description="Lint Python project or scripts using uv."
    )
    parser.add_argument(
        "pyscripts",
        nargs="*",
        default=(),
        help="An (optional) list of Python scripts to lint.",
    )
    parser.add_argument(
        "--pyright",
        action="store_const",
        const="pyright",
        default="ty",
        dest="type_checker",
        help="Use pyright as the type checker instead of the default ty.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def _find_pyscripts() -> Iterable[Path]:
    """Find Python scripts under the current directory,
    skipping virtual environment, build, cache and VCS directories.
    """
    EXCLUDED_DIRS = frozenset(
        {
            "venv",
            ".venv",
            "build",
            "dist",
            "node_modules",
            "__pycache__",
            "site-packages",
            ".git",
            ".jj",
            ".hg",
            ".svn",
            ".tox",
            ".nox",
            ".eggs",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
            ".ipynb_checkpoints",
        }
    )
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file.endswith(".py"):
                yield Path(root, file)


def uv_lint(pyscripts: Sequence[str | Path], type_checker: str) -> None:
    plus35 = "+" * 35
    line = "\n\n" + plus35 + "{}" + plus35 + "\n"
    if Path("pyproject.toml").exists():
        print(line.format(" pyproject-fmt "))
        sp.run(["uv", "run", "pyproject-fmt", "pyproject.toml"], check=True)
        print(line.format(" ruff check "))
        sp.run(
            ["uv", "run", "ruff", "check", "--fix", "--exit-non-zero-on-fix"],
            check=True,
        )
        print(line.format(" ruff format "))
        sp.run(["uv", "run", "ruff", "format"], check=True)
        if type_checker == "ty":
            print(line.format(" ty "))
            sp.run(["uv", "run", "ty", "check"], check=True)
        else:
            print(line.format(" pyright "))
            sp.run(["uv", "run", "pyright"], check=True)
        print(line.format(" deptry "))
        sp.run(["uv", "run", "deptry", "."], check=True)
        print(line.format(" pytest "))
        sp.run(["uv", "run", "pytest"], check=True)
        return
    if not pyscripts:
        pyscripts = list(_find_pyscripts())
    for pyscript in pyscripts:
        pyscript = Path(pyscript)
        print(line.format(f" {pyscript} "))
        print(line.format(" ruff check "))
        sp.run(
            [
                "uv",
                "run",
                "--with",
                "ruff",
                "--with-requirements",
                pyscript,
                "ruff",
                "check",
                "--fix",
                "--exit-non-zero-on-fix",
                pyscript,
            ],
            check=True,
        )
        print(line.format(" ruff format "))
        sp.run(
            [
                "uv",
                "run",
                "--with",
                "ruff",
                "--with-requirements",
                pyscript,
                "ruff",
                "format",
                pyscript,
            ],
            check=True,
        )
        if type_checker == "ty":
            print(line.format(" ty "))
            sp.run(
                [
                    "uv",
                    "run",
                    "--with",
                    "ty",
                    "--with-requirements",
                    pyscript,
                    "ty",
                    "check",
                    pyscript,
                ],
                check=True,
            )
        else:
            print(line.format(" pyright "))
            sp.run(
                [
                    "uv",
                    "run",
                    "--with",
                    "pyright",
                    "--with-requirements",
                    pyscript,
                    "pyright",
                    pyscript,
                ],
                check=True,
            )
        if not re.search(
            r"^\s*def test_\w+\(",
            pyscript.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            continue
        print(line.format(" pytest "))
        sp.run(
            [
                "uv",
                "run",
                "--with",
                "pytest",
                "--with-requirements",
                pyscript,
                "pytest",
                pyscript,
            ],
            check=True,
        )


def main():
    args = parse_args()
    uv_lint(args.pyscripts, args.type_checker)


if __name__ == "__main__":
    main()
