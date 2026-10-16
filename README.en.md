<div align="center">

# vLLM-Ascend Workspace

**A lightweight, multi-worktree local development scaffold for `vLLM` and `vLLM-Ascend` engineering**  
*面向 `vLLM` 与 `vLLM-Ascend` 多任务并行开发的轻量本地工作区脚手架*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](LICENSE)
[![vLLM](https://img.shields.io/badge/Upstream-vLLM-00A8E8?style=flat-square)](https://github.com/vllm-project/vllm)
[![vLLM-Ascend](https://img.shields.io/badge/Upstream-vLLM--Ascend-FF6B35?style=flat-square)](https://github.com/vllm-project/vllm-ascend)
[![MindIE Agent](https://img.shields.io/badge/Ecosystem-MindIE_Agent-6366F1?style=flat-square)](https://github.com/mindie-agent/mindie-agent)

**[简体中文](README.md)** · **English** · **[Script Reference](.agents/scripts/README.md)** · **[Task Example](.agents/examples/task)** · **[Contributing](CONTRIBUTING.md)**

</div>

---

## 💡 Why Use This Workspace?

When developing features, adapting operators, or reviewing PRs for `vLLM-Ascend`, you often need to **inspect `vllm` and `vllm-ascend` side by side** or **work on multiple independent bugfixes concurrently**.

`vllm-ascend-workspace` gives you a clean, repeatable local setup:
- **Paired Dual-Repo Management**: Tracks `vllm` and `vllm-ascend` upstream baselines as submodules and binds `origin` to your personal GitHub forks in one command.
- **Isolated Task Worktrees**: Creates lightweight Git worktrees under `.worktrees/<task>/` for each task—no more constant `git stash` juggling or cloning multiple multi-gigabyte checkouts.
- **Ready for AI Coding Agents**: Ships pre-configured rule entrypoints for `.claude/`, `.codex/`, `.cursor/`, `.trae/`, and `AGENTS.md`, working seamlessly alongside [MindIE Agent](https://github.com/mindie-agent/mindie-agent).

```mermaid
flowchart TB
    Root["vllm-ascend-workspace root"] --> Sub["Baseline Submodules<br/>vllm/ & vllm-ascend/"]
    Root --> WT[".worktrees/ Concurrent Task Worktrees"]
    WT --> T1[".worktrees/fix-moe/<br/>├── vllm-ascend (feature branch)<br/>└── vllm (paired baseline)"]
    WT --> T2[".worktrees/perf-decode/<br/>├── vllm-ascend (feature branch)<br/>└── vllm (paired baseline)"]
```

---

## ⚡ Quick Start

### Option 1: One-Sentence Setup via Your AI Agent (Recommended)

Paste the following sentence into **Claude Code**, **OpenAI Codex CLI**, **Kimi Code**, or **Cursor**:

```text
Please initialize this vLLM-Ascend development workspace for me: https://github.com/mindie-agent/vllm-ascend-workspace
```

<details>
<summary>🤖 <b>AI Agent Auto-Setup Protocol (Instructions for AI Agents)</b></summary>

When the user asks you to set up `vllm-ascend-workspace`, execute the following steps automatically:

1. **Clone or enter the workspace repository**:
   ```bash
   git clone https://github.com/mindie-agent/vllm-ascend-workspace.git
   cd vllm-ascend-workspace
   ```
2. **Detect the user's GitHub username and initialize submodules & fork remotes**:
   - Check `gh api user -q .login` first; ask the user only if `gh` is unavailable.
   - Run non-interactive initialization:
     ```bash
     python3 .agents/scripts/repo_init.py --github-user <GITHUB_USERNAME> --no-input
     ```
3. **Create an isolated task worktree on demand when starting a task**:
   ```bash
   python3 .agents/scripts/workspace.py task-init .worktrees/<task-name> --title "<task-name>"
   python3 .agents/scripts/workspace.py worktree-add vllm-ascend .worktrees/<task-name>/vllm-ascend --ref HEAD --branch feat/<task-name>
   ```

</details>

---

### Option 2: Manual Terminal Setup (For Humans)

#### 1. Initialize Submodules & Configure Your Forks

```bash
# Interactive prompt for your GitHub username or fork URLs
python3 .agents/scripts/repo_init.py

# Or pass your GitHub username directly (sets origin -> your fork, upstream -> vllm-project)
python3 .agents/scripts/repo_init.py --github-user YOUR_GITHUB_USER --no-input
```

Your choices are saved under `forks` in local `workspace.json` and reused automatically on future runs.

#### 2. Create an Isolated Worktree for a Task

```bash
# 1. Initialize a task directory
python3 .agents/scripts/workspace.py task-init .worktrees/demo --title demo

# 2. Add worktrees for vllm-ascend and vllm (check .github/vllm-main-verified.commit for the paired vLLM ref)
python3 .agents/scripts/workspace.py worktree-add vllm-ascend .worktrees/demo/vllm-ascend --ref HEAD --branch codex/demo
python3 .agents/scripts/workspace.py worktree-add vllm .worktrees/demo/vllm --ref HEAD
```

---

## 📁 Directory Layout

```text
.
├── vllm/                    # vLLM source submodule (upstream -> vllm-project/vllm)
├── vllm-ascend/             # vLLM-Ascend source submodule (upstream -> vllm-project/vllm-ascend)
├── .worktrees/              # Isolated development worktrees per task
├── .vaws-local/             # Local notes, temporary data, and persistent results
├── tools/                   # Optional standalone tool and skill repositories
├── .agents/                 # Shared agent configuration, helper scripts, and examples
│   ├── scripts/             # repo_init.py and workspace.py scripts + documentation
│   └── examples/            # Adaptable task workflow examples
├── .claude/                 # Claude Code project configuration and rule entrypoints
├── .codex/                  # OpenAI Codex project configuration templates
├── .cursor/                 # Cursor project configuration and rule entrypoints
├── .trae/                   # Trae project configuration and rule entrypoints
├── workspace.json.example   # Personal workspace configuration template
├── AGENTS.md                # Agent guidance for workspace development
├── CONTRIBUTING.md          # Workspace scaffold maintenance guide (English)
└── CONTRIBUTING.zh.md       # Workspace scaffold maintenance guide (Chinese)
```

See [`.agents/scripts/README.md`](.agents/scripts/README.md) ([中文](.agents/scripts/README.zh.md)) for full helper command options and [`.agents/examples/task`](.agents/examples/task) ([中文](.agents/examples/task/README.zh.md)) for a complete walkthrough.

---

## 🤝 Contributing

Before modifying helper scripts, configuration templates, or documentation in this scaffold, please read [`CONTRIBUTING.md`](CONTRIBUTING.md) ([中文](CONTRIBUTING.zh.md)). Code contributions to `vLLM` and `vLLM-Ascend` follow the upstream guidelines in their respective repositories.
