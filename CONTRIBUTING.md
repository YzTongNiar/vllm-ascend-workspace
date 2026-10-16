# Contributing to the workspace

[中文](CONTRIBUTING.zh.md) | English

Read this guide when maintaining this workspace repository's helper scripts, configuration templates, shared agent resources, or documentation. Contributions to vLLM and vLLM Ascend follow the guidance in the corresponding source repository at the selected revision.

## Implementation and validation

- Validate scaffold changes with disposable local repositories and directories. Run hardware-dependent checks in an environment with the required devices and runtime.
- When changing helper behavior, keep command help, examples, and affected command and path documentation aligned with the implementation.
- For helper script changes, run the local checks from the workspace root. Repository initialization tests use disposable local Git remotes:

  ```bash
  python3 -m unittest discover -s .agents/scripts/tests -v
  ```

## Shared agent resources

- Maintain shared content at its owning source. When editing a skill, update the affected instructions, scripts, references, assets, and tests together.
- Keep client-specific entry points small and use relative links for shared resources where supported.
- Keep reusable instructions separate from task progress and experiment records.

## Documentation

- Maintain Chinese `README.md` as the default at the repository root and English `README.en.md` with matching examples and reciprocal links; maintain English `CONTRIBUTING.md` and subdirectory `README.md` files alongside Chinese `.zh.md` counterparts.
- Write this workspace's `AGENTS.md` and shared agent instructions in English. Choose the language of task records according to the task and user requirements.
