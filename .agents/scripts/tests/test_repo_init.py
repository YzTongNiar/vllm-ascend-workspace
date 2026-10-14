"""Exercise initialization against disposable local Git repositories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "repo_init.py"
NAMES = ("vllm", "vllm-ascend")


class RepoInitTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workspace-init-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "2",
                    "GIT_CONFIG_KEY_0": "protocol.file.allow", "GIT_CONFIG_VALUE_0": "always",
                    "GIT_CONFIG_KEY_1": f"url.file://{self.base}/upstream/.insteadOf",
                    "GIT_CONFIG_VALUE_1": "https://github.com/vllm-project/",
                    "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        seed = self.base / "seed"
        seed.mkdir()
        self.git(seed, "init", "-b", "main")
        (seed / "source.txt").write_text("initial\n")
        self.git(seed, "add", ".")
        self.git(seed, "commit", "-m", "fixture")
        (self.base / "upstream").mkdir()
        template = self.base / "template"
        template.mkdir()
        self.git(template, "init", "-b", "main")
        for name in NAMES:
            self.git(self.base, "clone", "--bare", str(seed), str(self.base / "upstream" / f"{name}.git"))
            self.git(template, "submodule", "add", f"https://github.com/vllm-project/{name}.git", name)
        (template / "workspace.json.example").write_text(json.dumps({"tools": {"custom": "tools/custom"}}))
        self.git(template, "add", ".")
        self.git(template, "commit", "-m", "workspace")
        self.root = self.base / "workspace"
        self.git(self.base, "clone", str(template), str(self.root))
        self.modules = (self.root / ".gitmodules").read_bytes()

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def run_init(self, *args, answers="", success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args],
                                cwd=self.base, env=self.env, input=answers,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return json.loads(result.stdout), result.stderr

    def test_interactive_username_initializes_and_persists(self):
        result, prompts = self.run_init(answers="alice\n")
        self.assertIn("GitHub username", prompts)
        self.assertEqual(result["initialized"], list(NAMES))
        for name in NAMES:
            repo = self.root / name
            self.assertEqual(self.git(repo, "remote", "get-url", "origin"), f"https://github.com/alice/{name}.git")
            self.assertEqual(self.git(repo, "config", "--get", "remote.upstream.url"),
                             f"https://github.com/vllm-project/{name}.git")
            self.assertEqual(self.git(repo, "rev-parse", "HEAD"), self.git(self.root, "rev-parse", f"HEAD:{name}"))
        config = json.loads((self.root / "workspace.json").read_text())
        self.assertEqual(config["tools"], {"custom": "tools/custom"})
        self.assertEqual(config["forks"], {name: f"https://github.com/alice/{name}.git" for name in NAMES})
        self.assertEqual((self.root / ".gitmodules").read_bytes(), self.modules)

    def test_individual_forks_and_saved_rerun_preserve_checkout(self):
        self.run_init(answers="\nalice/custom-vllm\nhttps://github.com/bob/ascend-fork.git\n")
        repo = self.root / "vllm"
        self.git(repo, "checkout", "-b", "local-work")
        (repo / "source.txt").write_text("local commit\n")
        self.git(repo, "commit", "-am", "local change")
        head = self.git(repo, "rev-parse", "HEAD")
        (repo / "source.txt").write_text("unfinished work\n")
        self.git(repo, "config", "remote.origin.pushurl", "https://github.com/old/wrong.git")
        result, prompts = self.run_init("--no-input")
        self.assertEqual(result["initialized"], [])
        self.assertNotIn("GitHub username", prompts)
        self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(repo, "branch", "--show-current"), "local-work")
        self.assertEqual((repo / "source.txt").read_text(), "unfinished work\n")
        self.assertEqual(self.git(repo, "remote", "get-url", "--push", "origin"), "https://github.com/alice/custom-vllm.git")
        self.assertEqual(result["repositories"]["vllm-ascend"]["origin"], "https://github.com/bob/ascend-fork.git")
        self.assertEqual((self.root / ".gitmodules").read_bytes(), self.modules)

    def test_cli_precedence_and_existing_upstream(self):
        self.run_init("--github-user", "alice", "--no-input")
        result, _ = self.run_init("--github-user", "bob", "--vllm-fork", "carol/custom", "--no-input")
        self.assertEqual(result["repositories"]["vllm"]["origin"], "https://github.com/carol/custom.git")
        self.assertEqual(result["repositories"]["vllm-ascend"]["origin"], "https://github.com/bob/vllm-ascend.git")
        for name in NAMES:
            self.assertEqual(self.git(self.root / name, "remote").splitlines(), ["origin", "upstream"])

    def test_missing_input_fails_before_mutation(self):
        before = self.git(self.root, "config", "--local", "--list")
        for args in [("--no-input",), ()]:
            result, _ = self.run_init(*args, success=False)
            self.assertIn("error", result)
            self.assertFalse((self.root / "workspace.json").exists())
            self.assertEqual(self.git(self.root, "config", "--local", "--list"), before)
            for name in NAMES:
                self.assertFalse((self.root / name / ".git").exists())


if __name__ == "__main__":
    unittest.main()
