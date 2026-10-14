# Workspace helper scripts

`repo_init.py` initializes source repositories and fork remotes. `workspace.py` provides independently callable filesystem and Git worktree operations. Both use Python 3 and Git; worktree creation requires `git worktree add --relative-paths` support.

## Repository initialization

Run `python3 .agents/scripts/repo_init.py` from the workspace root. It asks for a GitHub username, or individual fork URLs / `OWNER/REPOSITORY` values. Supply your existing forks. A username or shorthand produces HTTPS URLs; explicit Git URLs are used as supplied.

```bash
python3 .agents/scripts/repo_init.py --github-user YOUR_GITHUB_USER --no-input
python3 .agents/scripts/repo_init.py --vllm-fork OWNER/vllm --vllm-ascend-fork OWNER/vllm-ascend --no-input
```

The script initializes missing `vllm` and `vllm-ascend` submodules at the workspace's recorded commits. Existing checkouts, branches and edits are retained. It configures each `origin` for the selected fork and `upstream` for `https://github.com/vllm-project/<repository>.git`, clearing separate push-URL overrides so fetch and push use those destinations. `.gitmodules` keeps the community URLs. Linked source worktrees share these remote settings.

Fork choices are persisted in the ignored `workspace.json` under `forks.vllm` and `forks.vllm-ascend`. A new config starts from `workspace.json.example` when available; existing fields are retained. Explicit fork options take precedence over `--github-user`, followed by saved choices. Missing choices prompt the user; `--no-input` reports them before changing repositories. Agents should ask the user and pass the answers as arguments when interactive input is unavailable.

`--root PATH` selects the workspace; by default it is located from the script, independent of the calling directory. Progress and prompts use stderr; the result is JSON on stdout. Initialization is separate from `workspace.py task-init`, which creates an individual task directory.

## Paths and configuration

The default path base is the workspace containing this script. Relative directory arguments and configured repository paths use that base even when the command is launched from another working directory. `--root PATH` selects another workspace; a relative `--root` is resolved from the calling directory. Put global options before the operation name.

Worktree operations accept a repository path or a name from the `repositories` mapping in `workspace.json`. `--config PATH` selects another configuration file relative to the workspace root. Direct repository paths can be used without a configuration file. Task and directory operations use their supplied paths independently of that configuration.

Git worktree links and task symlinks use relative paths. Paths stored in a task's metadata are relative to the task directory.

## Operations

| Command | Operation |
|---|---|
| `worktree-add REPOSITORY DIRECTORY --ref REF` | Add a detached worktree; `--branch NAME` creates a branch; the default ref is `HEAD` |
| `task-init DIRECTORY --title TITLE` | Create a directory and an editable `task.json`; the default title is the directory name |
| `worktree-remove REPOSITORY DIRECTORY` | Use Git to remove the specified worktree and its registration |
| `directory-remove DIRECTORY` | Remove the specified directory; for a symlink, remove the link itself |

Task initialization accepts `--records PATH` and `--results PATH` to create target directories and relative symlinks. Existing task metadata or occupied link names produce an error so their contents are preserved. Task fields can be extended as needed.

Both removal commands support `--dry-run` to show the target. For worktree removal, `--force` is passed directly to Git and can be repeated; native Git errors are returned to the caller. Removing a worktree preserves its branch. Directory removal deletes the selected filesystem directory and its contents; symlink targets remain intact. The workspace root and its ancestors are protected from ordinary directory removal.

## Examples

Run these examples from the workspace root. From another directory, use the actual path to `workspace.py`; its argument path base stays the same.

```bash
python3 .agents/scripts/workspace.py --help
python3 .agents/scripts/workspace.py task-init .worktrees/demo --title demo
python3 .agents/scripts/workspace.py worktree-add vllm .worktrees/demo/vllm --ref HEAD
python3 .agents/scripts/workspace.py worktree-remove vllm .worktrees/demo/vllm --dry-run
python3 .agents/scripts/workspace.py worktree-remove vllm .worktrees/demo/vllm
python3 .agents/scripts/workspace.py directory-remove .worktrees/demo
```

Optional record links can be selected when initializing a task:

```bash
python3 .agents/scripts/workspace.py task-init .worktrees/experiment --records .vaws-local/tasks/experiment/records --results .vaws-local/tasks/experiment/runs
```

## Results and maintenance

Commands write one JSON result to stdout and execution messages to stderr. Failures return a nonzero exit status and an error result; argument parsing errors use the CLI's usage output. Read the result before issuing a dependent operation.

When changing an operation, keep its help, examples, and documented behavior aligned. Check filesystem and Git behavior with disposable local directories and repositories.

Run repository initialization checks locally; their Git remotes use disposable local repositories:

```bash
python3 -m unittest discover -s .agents/scripts/tests -v
```
