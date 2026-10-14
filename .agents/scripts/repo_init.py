#!/usr/bin/env python3
"""Initialize source submodules with personal origins and community upstreams."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

REPOSITORIES = ("vllm", "vllm-ascend")


def git(root: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode not in allowed:
        raise RuntimeError(f"git {' '.join(args[:2])} exited with status {result.returncode}")
    return result.stdout.strip()


def fork_url(value: str) -> str:
    value = value.strip()
    if not value or value.startswith("-") or any(c.isspace() for c in value):
        raise ValueError("Provide a fork URL or GitHub OWNER/REPOSITORY.")
    if "://" in value or value.startswith("git@"):
        return value
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        return f"https://github.com/{value.removesuffix('.git')}.git"
    raise ValueError("Provide a fork URL or GitHub OWNER/REPOSITORY.")


def username(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", value):
        raise ValueError("Provide a GitHub username or organization name.")
    return value


def ask(prompt: str) -> str:
    print(prompt, file=sys.stderr, end="", flush=True)
    try:
        return input().strip()
    except EOFError as exc:
        raise ValueError(
            "Fork details are required. Ask the user, then pass --github-user "
            "or --vllm-fork and --vllm-ascend-fork."
        ) from exc


def choose_forks(args: argparse.Namespace, settings: dict) -> dict[str, str]:
    saved = settings.get("forks", {})
    if not isinstance(saved, dict):
        raise ValueError("workspace.json forks must be an object.")
    owner = username(args.github_user) if args.github_user else None
    values = {}
    for name in REPOSITORIES:
        explicit = getattr(args, name.replace("-", "_") + "_fork")
        value = explicit or (f"{owner}/{name}" if owner else saved.get(name))
        if value:
            values[name] = fork_url(value)
    missing = [name for name in REPOSITORIES if name not in values]
    if missing and args.no_input:
        raise ValueError(
            "Missing fork details for " + ", ".join(missing)
            + "; provide --github-user or the corresponding --*-fork options."
        )
    if missing:
        owner = ask("GitHub username for missing forks (blank to enter URLs): ")
        if owner:
            owner = username(owner)
        for name in missing:
            values[name] = fork_url(
                f"{owner}/{name}" if owner else ask(f"{name} fork URL or OWNER/REPOSITORY: ")
            )
    return values


def set_remote(repo: Path, name: str, url: str) -> None:
    if name not in git(repo, "remote").splitlines():
        git(repo, "remote", "add", name, url)
    else:
        git(repo, "config", "--local", "--replace-all", f"remote.{name}.url", url)
    # An old push URL would otherwise override the selected fork/upstream.
    git(repo, "config", "--local", "--unset-all", f"remote.{name}.pushurl", allowed=(0, 5))


def run(args: argparse.Namespace) -> dict:
    root = args.root.resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("--root must point to the workspace Git repository.")
    state = git(root, "submodule", "status", "--", *REPOSITORIES)
    modules = {line.split()[1]: line[0] for line in state.splitlines() if line.strip()}
    if set(modules) != set(REPOSITORIES):
        raise ValueError("The workspace must register vllm and vllm-ascend submodules.")
    config = root / "workspace.json"
    source = config if config.exists() else root / "workspace.json.example"
    settings = json.loads(source.read_text()) if source.exists() else {}
    if not isinstance(settings, dict):
        raise ValueError("workspace.json must contain an object.")
    forks = choose_forks(args, settings)
    initialized = []
    for name in REPOSITORIES:
        if modules[name] == "-":
            git(root, "submodule", "update", "--init", "--", name)
            initialized.append(name)
    remotes = {}
    for name in REPOSITORIES:
        upstream = f"https://github.com/vllm-project/{name}.git"
        set_remote(root / name, "origin", forks[name])
        set_remote(root / name, "upstream", upstream)
        remotes[name] = {"origin": forks[name], "upstream": upstream}
    settings["forks"] = {**settings.get("forks", {}), **forks}
    config.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    return {"operation": "repo-init", "initialized": initialized,
            "repositories": remotes, "config": "workspace.json"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="workspace root (default: this script's workspace)")
    parser.add_argument("--github-user", help="GitHub owner of both forks; uses HTTPS")
    parser.add_argument("--vllm-fork", help="vLLM fork URL or GitHub OWNER/REPOSITORY")
    parser.add_argument("--vllm-ascend-fork", help="vLLM Ascend fork URL or GitHub OWNER/REPOSITORY")
    parser.add_argument("--no-input", action="store_true", help="require supplied or saved fork details")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, TypeError, AttributeError) as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"operation": "repo-init", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
