# Agent resources

This directory holds shared helper scripts, examples, and project-specific agent resources. Start with the entry relevant to the task.

| Entry | Purpose | Read when |
|---|---|---|
| [scripts/](scripts/README.md) | Independently callable workspace operations | Creating worktrees, initializing tasks, or cleaning directories |
| [examples/](examples/README.md) | Adaptable examples | Choosing a starting format for task records |

Optional skills can be installed or linked under `skills/<skill-name>/` using the selected client's discovery mechanism. A skill package has a `SKILL.md` with `name` and `description` in YAML frontmatter; it can also include `scripts/`, `references/`, and `assets/`. Choose a skill from its description, then read its instructions and the resources needed for the current task.

These paths organize files. Instruction and skill loading depend on the client, its configuration, and the starting directory. When starting an agent from a submodule or task worktree, check which instructions and skills it actually discovers; use explicit file references or the client's supported configuration to make the intended resources available.

Maintain shared content at its owning source. When editing a skill, update the affected instructions, scripts, references, assets, and tests together. Keep client-specific entry points small and use relative links for shared resources where supported.
