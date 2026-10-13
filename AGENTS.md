# Workspace guidance

- Before changing code in a submodule or task worktree, read that repository's `AGENTS.md` at its checked-out revision, if present, and any more specific `AGENTS.md` applicable to the target files. Consult its contribution instructions when preparing commits or PRs.
- `vllm/` and `vllm-ascend/` are separate source repositories referenced by submodules. Worktrees of the same repository share branches and remotes, while each has its own checkout. Use the repository and revision selected for the task.
- For vLLM or vLLM Ascend development, create worktrees of the source repositories inside a task directory under `.worktrees/`. Do not create a worktree of the entire workspace repository for these tasks. See [.worktrees/README.md](.worktrees/README.md) for the reference layout.
- Workspace helper paths are resolved from the script's workspace root, regardless of the calling directory. For worktree creation, task initialization or cleanup, read [.agents/scripts/README.md](.agents/scripts/README.md); `--root` selects another workspace.
- When using an installed skill, read its `SKILL.md` and the resources relevant to the task. For configuring discovery from different working directories, consult [.agents/README.md](.agents/README.md).
- Use native local tools for local work. Prefer available MindIE Agent tools for remote NPU operations. Observe remote jobs through the backend that created them; inspect the original receipt before retrying an uncertain operation.
- Validate scaffold changes with disposable local repositories and directories. Run hardware-dependent checks in an environment with the required devices and runtime.
- Cleanup acts on user-selected objects. Query PR status when the user wants that advice.
- Keep reusable instructions separate from task progress and experiment records. Update affected command and path documentation alongside implementation changes.
- Maintain Chinese `README.md` as the default and English `README.en.md` with matching examples and reciprocal links. Write AGENTS.md and other Markdown documentation in English.
