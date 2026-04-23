import argparse
import re
from pathlib import Path
import subprocess as sp


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(
        description="Set/overwrite key to have value in /etc/sysctl.conf."
    )
    parser.add_argument("key", help="The key to set or overwrite.")
    parser.add_argument("value", help="The value to set.")
    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        default="/etc/sysctl.conf",
        help="The path to the sysctl configuration file.",
    )
    parser.add_argument(
        "-a",
        "--apply",
        dest="apply",
        action="store_true",
        help="Whether to apply the changes by running 'sysctl -p'.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def _write_lines(lines: list[str], path: Path, apply: bool) -> None:
    with path.open("w", encoding="utf-8") as fout:
        fout.writelines(lines)
    if apply:
        sp.run(["sysctl", "-p", str(path)], check=True)


def etc_sysctl(
    key: str, value: str, path: str | Path = "/etc/sysctl.conf", apply: bool = False
) -> None:
    """Set/overwrite key to have value in /etc/sysctl.conf.

    :param key: The key to set or overwrite.
    :param value: The value (of key) to set.
    :param path: The path to the sysctl configuration file.
    :param apply: Whether to apply the changes by running 'sysctl -p'.
    """
    valid_values = {
        "kernel.perf_event_paranoid": ("-1", "0", "1", "2", "3"),
    }
    if key in valid_values:
        if value not in valid_values[key]:
            raise ValueError(
                f"Invalid value '{value}' for key '{key}'! "
                f"Valid values are {valid_values[key]}."
            )
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return _write_lines([f"{key} = {value}\n"], path, apply)
    with path.open("r", encoding="utf-8") as fin:
        lines = fin.readlines()
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key} = {value}\n"
            return _write_lines(lines, path, apply)
    lines.append(f"{key} = {value}\n")
    _write_lines(lines, path, apply)


def main():
    args = parse_args()
    etc_sysctl(args.key, args.value, path=args.path, apply=args.apply)


if __name__ == "__main__":
    main()
