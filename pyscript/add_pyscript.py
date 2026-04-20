"""Add a Python Script using the template."""
import argparse
import shutil
import subprocess as sp
from pathlib import Path


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(description="Add a new Gemini command.")
    parser.add_argument("name", help="The name of the Python script.")
    parser.add_argument(
        "-d",
        "--dir",
        dest="dir",
        default=".",
        help="The directory ('.' by default) within which to create the Python script.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def add_pyscript(name: str, dir_: str) -> Path:
    name = name.replace(" ", "_").replace("-", "_")
    dir_pyscript = Path(dir_)
    dir_pyscript.mkdir(exist_ok=True)
    path = dir_pyscript / f"{name}.py"
    if path.exists():
        print(f"The Python script {path} already exists.\n")
    else:
        text = (
            (Path(__file__).parent / "pyscript.txt")
            .read_text()
            .replace("my_function", name)
        )
        path.write_text(text)
        print(f"Created the Python script {path}.\n")
    return path


def main():
    args = parse_args()
    path = add_pyscript(args.name, args.dir)
    vim = "nvim" if shutil.which("nvim") else "vim"
    sp.run([vim, path], check=True)


if __name__ == "__main__":
    main()
