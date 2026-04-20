"""Gemini related utility functions."""
import argparse
import shutil
import subprocess as sp
from pathlib import Path


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(description="Add a new Gemini command.")
    parser.add_argument("name", help="The name of the Gemini command.")
    parser.add_argument(
        "-d",
        "--dir",
        dest="dir",
        default=".gemini",
        help="The directory ('.gemini' by default) within which to create the Python script.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def add_custom_command(name: str, dir_: str) -> Path:
    name = name.replace(" ", "_").replace("-", "_")
    dir_gemini = Path(dir_)
    dir_gemini.mkdir(exist_ok=True)
    path = dir_gemini / f"{name}.toml"
    if path.exists():
        print(f"The command {name} @ {path} already exists.\n")
    else:
        path.write_text('description = ""\nprompt = """"""\n')
        print(f"Created the command {name} @ {path}.\n")
    return path


def main():
    args = parse_args()
    path = add_custom_command(args.name, args.dir)
    vim = "nvim" if shutil.which("nvim") else "vim"
    sp.run([vim, path], check=True)


if __name__ == "__main__":
    main()
