import argparse
import re
import subprocess as sp
from pathlib import Path
from typing import Iterable


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
        "--ty",
        action="store_const",
        const="ty",
        default="pyright",
        dest="type_checker",
        help="Use ty as the type checker.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def uv_lint(pyscripts: Iterable[str] | Iterable[Path], type_checker: str) -> None:
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
        print(line.format(" ty "))
        sp.run(["uv", "run", "ty", "check"], check=True)
        print(line.format(" deptry "))
        sp.run(["uv", "run", "deptry", "."], check=True)
        print(line.format(" pytest "))
        sp.run(["uv", "run", "pytest"], check=True)
        return
    if not pyscripts:
        pyscripts = Path().glob("**/*.py")
    for pyscript in pyscripts:
        pyscript = str(pyscript)
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
            r"^\s*def test_\w+\(", Path(pyscript).read_text(), re.MULTILINE
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
