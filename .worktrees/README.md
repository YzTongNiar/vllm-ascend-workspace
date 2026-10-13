# Development directories

This directory holds source repository worktrees grouped into task working directories. For vLLM and vLLM Ascend development, each task directory contains the source worktrees needed for that task.

## Reference layout

```text
.worktrees/
└── feat-name/
    ├── AGENTS.md               # Task entry point, source locations, and data locations
    ├── vllm/                   # Task worktree at the paired vLLM revision
    ├── vllm-ascend/            # Task branch worktree
    ├── task.json -> ../../.vaws-local/tasks/<task-id>/task.json
    ├── records -> ../../.vaws-local/tasks/<task-id>/records/
    └── results -> ../../.vaws-local/tasks/<task-id>/runs/
```

`feat-name` is a readable directory name; `<task-id>` identifies the chosen task data directory. Adapt the names and included repositories to the task. The task directory groups its contents, while each source directory is a worktree of its own repository.

Keep the task's `AGENTS.md` brief: describe the task entry point, source paths, and data paths. For paired development, select the vLLM revision corresponding to the task's vLLM Ascend revision; its `.github/vllm-main-verified.commit` provides the pairing reference where available. Before editing, read the source repository's AGENTS.md at the checked-out revision and any applicable instructions closer to the target files.

The symlink targets above are relative to `feat-name/`. The helper's `task-init` command can create `records` and `results` links, and writes `task.json` locally. To use the metadata link shown here, place that file at the selected persistent location and create the relative link.

## Git operations

Worktrees of one repository share commits, branches, and remotes. Each worktree has its own files, HEAD, and index.

Git worktree removal updates both the checkout and its Git registration. Ordinary directory removal operates on filesystem contents. Select the operation for the object being removed.
