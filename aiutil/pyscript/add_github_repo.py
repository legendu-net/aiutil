import argparse
import os
import sys
from pathlib import Path
from dulwich import porcelain
from github_rest_api import User, Organization


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser(description="Add a GitHub repository.")
    parser.add_argument(
        "repo",
        help="The GitHub repo (in the format of owner/repo) to be created.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-u",
        "--user",
        dest="is_owner_user",
        action="store_true",
        help="The owner of the repo is a user.",
    )
    group.add_argument(
        "-o",
        "--org",
        "--organization",
        dest="is_owner_user",
        action="store_false",
        help="The owner of the repo is an organization.",
    )
    parser.add_argument(
        "-p",
        "--public",
        dest="private",
        action="store_false",
        help="Whether to create the repository as public.",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="dir",
        default=".",
        help="The directory within to create the local git repository.",
    )
    return parser.parse_args(args=args, namespace=namespace)


def create_remote_repo(
    repo: str, private: bool, token: str, is_owner_user: bool
) -> None:
    owner, repo = repo.strip().split("/")
    entity = (
        User(token=token, user=owner)
        if is_owner_user
        else Organization(token=token, org=owner)
    )
    entity.create_repository(name=repo, private=private)
    print(f"\nCreated the GitHub repo https://github.com/{repo}.\n")


def add_github_repo(
    repo: str, private: bool, is_owner_user: bool, dir_: str, token: str
) -> None:
    repo = repo.strip()
    create_remote_repo(
        repo=repo, private=private, token=token, is_owner_user=is_owner_user
    )
    # local git repo
    name = repo.split("/")[-1]
    path = Path(dir_) / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text(f"# {name}\n")
    porcelain.init(path=path)
    porcelain.add(repo=path)
    porcelain.commit(repo=path, message="first commit")

    def _create_push_branch(branch: str):
        porcelain.branch_create(repo=path, name=branch)
        porcelain.checkout(repo=path, target=branch)
        porcelain.push(
            repo=path,
            remote_location=f"https://{token}@github.com/{repo}.git",
        )

    _create_push_branch("dev")
    _create_push_branch("main")
    porcelain.checkout(repo=path, target="dev")
    porcelain.branch_delete(repo=path, name="main")
    porcelain.branch_delete(repo=path, name="master")


def main():
    args = parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN environment variable not set.")
        sys.exit(1)
    add_github_repo(
        repo=args.repo,
        private=args.private,
        is_owner_user=args.is_owner_user,
        dir_=args.dir,
        token=token,
    )


if __name__ == "__main__":
    main()
