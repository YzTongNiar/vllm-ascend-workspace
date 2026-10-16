# vLLM Ascend workspace

[简体中文](README.md) | English

A local development scaffold you can adapt to your workflow. The root repository maintains documentation, configuration templates, agent configuration, and helper scripts, with vLLM and vLLM Ascend referenced as submodules.

## Directory layout

```text
.
├── vllm/                    # vLLM source submodule for manual inspection
├── vllm-ascend/              # vLLM Ascend source submodule for manual inspection
├── .worktrees/               # Development worktrees and task working directories
├── .vaws-local/              # Local notes, temporary data, and persistent results
├── tools/                   # Independently installed and maintained tool and skill repositories
├── .agents/                 # Shared agent configuration, helper scripts, and examples
│   ├── scripts/             # Repository initialization, worktrees, and directory management
│   └── examples/            # Task examples to adapt as needed
├── .claude/                 # Claude project configuration and rule entry points
├── .codex/                  # Codex project configuration templates
├── .cursor/                 # Cursor project configuration and rule entry points
├── .trae/                   # Trae project configuration and rule entry points
├── .gitignore               # Files tracked by the root repository
├── .gitmodules              # Upstream URLs for the two source submodules
├── workspace.json.example   # Personal workspace configuration template
├── AGENTS.md                # Agent guidance for source development using the workspace
├── CONTRIBUTING.md          # Workspace scaffold maintenance guide (English)
├── CONTRIBUTING.zh.md       # Workspace scaffold maintenance guide (Chinese)
├── README.md                # Chinese documentation, the default entry point
└── README.en.md             # English documentation
```

## Usage

Initialize the source repositories and configure your forks:

```bash
python3 .agents/scripts/repo_init.py
```

The script asks for your GitHub username, or individual fork URLs / `OWNER/REPOSITORY` values. A username produces HTTPS URLs. Each source repository uses the selected fork as `origin` and `vllm-project` as `upstream`. Choices are saved under `forks` in local `workspace.json` and reused on subsequent runs; `.gitmodules` retains community upstream URLs.

You can also supply a username directly:

```bash
python3 .agents/scripts/repo_init.py --github-user YOUR_GITHUB_USER --no-input
```

`workspace.json` holds personal configuration. The `repositories` mapping can define aliases for repository arguments in the helper script; configured paths are resolved relative to the workspace root. The `tools` mapping can record paths to tools you install yourself.

The source checkouts at the root are available for inspection. The following commands illustrate creating a development directory and adding worktrees for both source repositories. Choose refs and branch names to suit the task.

```bash
python3 .agents/scripts/workspace.py task-init .worktrees/demo --title demo
python3 .agents/scripts/workspace.py worktree-add vllm-ascend .worktrees/demo/vllm-ascend --ref HEAD --branch codex/demo
python3 .agents/scripts/workspace.py worktree-add vllm .worktrees/demo/vllm --ref HEAD
```

The script resolves paths relative to its workspace and can be invoked from any working directory. Use `--root` to select another workspace. Command arguments select the source revisions. For paired Ascend development, consult `.github/vllm-main-verified.commit` at the selected Ascend revision when choosing the vLLM ref.

See [.agents/scripts/README.md](.agents/scripts/README.md) ([中文](.agents/scripts/README.zh.md)) for helper commands and options, and [.agents/examples/task](.agents/examples/task) ([中文](.agents/examples/task/README.zh.md)) for a task example. You can place tools and skills in `tools/` and maintain each as an independent Git repository.

## Maintaining the workspace

Before changing this workspace's helper scripts, configuration templates, shared agent resources, or documentation, read [CONTRIBUTING.md](CONTRIBUTING.md) ([中文](CONTRIBUTING.zh.md)) for validation requirements and documentation conventions. Contributions to vLLM and vLLM Ascend follow the guidance in their respective source repositories.
