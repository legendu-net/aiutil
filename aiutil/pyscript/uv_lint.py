#!/usr/bin/env -S uv run
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
# ]
# ///
import argparse
from pathlib import Path
import re
import subprocess as sp
from typing import Iterable


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(description="<DESCRIPTION>")
    parser.add_argument(
        "pyscripts",
        nargs="*",
        default=(),
        help="An (optional) list of Python scripts to lint.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def uv_lint(pyscripts: Iterable[str] | Iterable[Path]) -> None:
    plus35 = "+" * 35
    line = "\n\n" + plus35 + "{}" + plus35 + "\n"
    if Path("pyproject.toml").exists():
        print(line.format(" pyproject-fmt "))
        sp.run("uv run pyproject-fmt pyproject.toml", shell=True, check=True)
        print(line.format(" ruff check "))
        sp.run("uv run ruff check", shell=True, check=True)
        print(line.format(" ruff format "))
        sp.run("uv run ruff format", shell=True, check=True)
        print(line.format(" ty "))
        sp.run("uv run ty check", shell=True, check=True)
        print(line.format(" deptry "))
        sp.run("uv run deptry .", shell=True, check=True)
        print(line.format(" pytest "))
        sp.run("uv run pytest", shell=True, check=True)
        return
    if not pyscripts:
        pyscripts = Path().glob("**/*.py")
    for pyscript in pyscripts:
        print(line.format(f" {pyscript} "))
        print(line.format(" ruff check "))
        sp.run(
            f"uv run --with ruff --with-requirements '{pyscript}' ruff check '{pyscript}'",
            shell=True,
            check=True,
        )
        print(line.format(" ruff format "))
        sp.run(
            f"uv run --with ruff --with-requirements '{pyscript}' ruff format '{pyscript}'",
            shell=True,
            check=True,
        )
        print(line.format(" ty "))
        sp.run(
            f"uv run --with ty --with-requirements '{pyscript}' ty check '{pyscript}'",
            shell=True,
            check=True,
        )
        if not re.search(r"^\s*def test_\w+\(", Path(pyscript).read_text()):
            continue
        print(line.format(" pytest "))
        sp.run(
            f"uv run --with pytest --with-requirements '{pyscript}' pytest check '{pyscript}'",
            shell=True,
            check=True,
        )


def main():
    args = parse_args()
    uv_lint(args.pyscripts)


if __name__ == "__main__":
    main()
