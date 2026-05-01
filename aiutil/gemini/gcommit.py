import argparse
import os
import subprocess as sp
import sys


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(
        description="Automatically commit staged changes with a generated message."
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show the commit message without committing staged changes.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def gcommit(dry_run: bool) -> None:
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("Error: GEMINI_API_KEY environment variable is not set.")

    diff = sp.run(
        ["git", "diff", "--staged"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if not diff:
        print("No staged changes to commit.")
        return

    print("Generating commit message...")
    process = sp.run(
        [
            "gemini",
            "-p",
            "Write a concise Conventional Commit message for this diff. Output ONLY the message.",
        ],
        input=diff,
        capture_output=True,
        text=True,
        check=True,
    )
    msg = process.stdout.strip()
    if not msg:
        print("Failed to generate a message.")
        return
    print(f"Commit message: {msg}")
    if dry_run:
        print("Changes are not committed due to the dry run mode.")
        return
    sp.run(["git", "commit", "-m", msg], check=True)


def main():
    args = parse_args()
    gcommit(args.dry_run)


if __name__ == "__main__":
    main()
