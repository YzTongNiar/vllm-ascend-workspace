#!/usr/bin/env python3
"""Local filesystem and Git worktree operations with workspace-relative paths."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def path_at(root: Path, value: str) -> Path:
    # Keep the final component intact so removing a link removes the link itself.
    return Path(os.path.abspath(root / value))


def relative(root: Path, path: Path) -> str:
    return os.path.relpath(path, root)


def git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True
    )
    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode:
        raise RuntimeError(f"git exited with status {result.returncode}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                   help="workspace root (default: this script's workspace)")
    p.add_argument("--config", help="JSON configuration path relative to root")
    commands = p.add_subparsers(dest="command", required=True)
    add = commands.add_parser("worktree-add", help="create a Git worktree")
    add.add_argument("repository", help="repository path or configured name")
    add.add_argument("directory")
    add.add_argument("--ref", default="HEAD")
    add.add_argument("--branch", help="create this branch; otherwise detach HEAD")
    remove = commands.add_parser("worktree-remove", help="remove a Git worktree")
    remove.add_argument("repository", help="repository path or configured name")
    remove.add_argument("directory")
    remove.add_argument("--force", action="count", default=0,
                        help="pass --force to Git; repeat for a locked worktree")
    remove.add_argument("--dry-run", action="store_true")
    task = commands.add_parser("task-init", help="create a task directory and metadata")
    task.add_argument("directory")
    task.add_argument("--title")
    task.add_argument("--records", help="create a records link to this directory")
    task.add_argument("--results", help="create a results link to this directory")
    delete = commands.add_parser("directory-remove", help="remove a directory or link")
    delete.add_argument("directory")
    delete.add_argument("--dry-run", action="store_true")
    return p


def run(args: argparse.Namespace) -> dict:
    root = args.root.resolve()
    directory = path_at(root, args.directory)
    result = {"operation": args.command, "directory": relative(root, directory)}

    if args.command.startswith("worktree-"):
        config = path_at(root, args.config) if args.config else root / "workspace.json"
        settings = json.loads(config.read_text()) if config.exists() else {}
        if args.config and not config.is_file():
            raise FileNotFoundError(config)
        repo = path_at(root, settings.get("repositories", {}).get(
            args.repository, args.repository))
        result["repository"] = relative(root, repo)
        if args.command == "worktree-add":
            options = ["-b", args.branch] if args.branch else ["--detach"]
            git(repo, "worktree", "add", "--relative-paths", *options,
                "--", str(directory), args.ref)
        else:
            result["dry_run"] = args.dry_run
            if not args.dry_run:
                git(repo, "worktree", "remove", *(["--force"] * args.force),
                    "--", str(directory))
    elif args.command == "task-init":
        links = {name: path_at(root, value) for name, value in
                 (("records", args.records), ("results", args.results)) if value}
        metadata = directory / "task.json"
        # Report collisions before creating any task files.
        for item in [metadata, *(directory / name for name in links)]:
            if os.path.lexists(item):
                raise FileExistsError(item)
        for name, target in links.items():
            location = directory / name
            resolved = target.resolve()
            if resolved == directory.resolve() or resolved in location.resolve().parents:
                raise ValueError(f"{name}: link target would contain its own link")
            if location.resolve() == resolved or location.resolve() in resolved.parents:
                raise ValueError(f"{name}: link target is inside its link location")
        directory.mkdir(parents=True, exist_ok=True)
        content = {"title": args.title if args.title is not None else directory.name}
        if links:
            content["paths"] = {name: relative(directory, target)
                                for name, target in links.items()}
        for name, target in links.items():
            target.mkdir(parents=True, exist_ok=True)
            (directory / name).symlink_to(relative(directory, target),
                                          target_is_directory=True)
        with metadata.open("x") as stream:
            stream.write(json.dumps(content, ensure_ascii=False, indent=2) + "\n")
    elif args.command == "directory-remove":
        result["dry_run"] = args.dry_run
        if not args.dry_run:
            if directory.is_symlink():
                directory.unlink()
            elif directory.resolve() == root or directory.resolve() in root.parents:
                raise ValueError("select a directory below or beside the workspace root")
            else:
                shutil.rmtree(directory)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, TypeError, AttributeError) as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"operation": args.command, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
