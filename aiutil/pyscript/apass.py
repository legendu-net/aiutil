"""Run commands without the need to enter password (repeatedly)."""

import argparse
import base64
import datetime
import getpass
import json
import math
import sys
import time
from pathlib import Path
from typing import Iterable

import pexpect
import yaml

CONFIG_DIR = Path.home() / ".config" / "apass"
PATH_CONFIG = CONFIG_DIR / "profile.json"
PATH_PROMPTS = CONFIG_DIR / "prompts.yml"

USER = getpass.getuser()
FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def _get_prompts() -> dict[str, str]:
    if not PATH_PROMPTS.is_file():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with PATH_PROMPTS.open("w", encoding="utf-8") as fout:
            yaml.dump({}, fout, default_flow_style=False)
    # read prompts
    with PATH_PROMPTS.open("r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f) or {}
    return {k: v.format(USER=USER) for k, v in prompts.items()}


def _get_password(timeout: float) -> str:
    if PATH_CONFIG.is_file():
        token = json.loads(PATH_CONFIG.read_text(encoding="utf-8"))
        time_token = datetime.datetime.strptime(token["time"], FORMAT)
        if (datetime.datetime.now() - time_token).total_seconds() <= timeout:
            return base64.b64decode(token["password"]).decode()
    token_time = datetime.datetime.now()
    passwd = getpass.getpass("Please enter your password: ")
    token = {
        "password": base64.b64encode(passwd.encode()).decode(),
        "time": token_time.strftime(FORMAT),
    }
    PATH_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    PATH_CONFIG.write_text(json.dumps(token, indent=4))
    return passwd


def _apass(command: Iterable[str], passwd: str):
    command = " ".join(command)
    prompts = _get_prompts()
    if not command:
        if not prompts:
            sys.exit(
                f"Error: No command is provided and no prompts are configured in {PATH_PROMPTS}."
            )
        command = next(iter(prompts))
    if command not in prompts:
        sys.exit(f"Error: Prompt for command '{command}' not found in {PATH_PROMPTS}")

    print("Auto filling password for the command", command)
    child = pexpect.spawn(command)
    child.logfile_read = sys.stdout.buffer
    child.expect(prompts[command])
    time.sleep(0.3)
    child.sendline(passwd)
    child.interact()


def parse_args():
    parser = argparse.ArgumentParser(
        description="A tool to run commands without entering your password repeatedly."
    )
    parser.add_argument(
        "command",
        nargs="*",
        default=(),
        help="The command to execute (defaults to the first command in prompts configuration).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    _apass(args.command, _get_password(timeout=math.inf))


if __name__ == "__main__":
    main()
