# Local tools

This directory can hold tool and skill repositories that you install and maintain independently.

| Example repository | Purpose |
|---|---|
| `benchmark` | Model accuracy and serving performance evaluation |
| `aisbench_auto_tools` | AISBench workloads and experiment helpers |
| `cannbot-skills` | CANN development and optimization skills |
| `vllm-ascend-skills` | vLLM Ascend development, validation, debugging, and analysis skills |

Choose the repositories and revisions needed for your work. Read each installed project's README for setup and dependencies, and its applicable AGENTS.md before modifying code. For a selected skill, read its SKILL.md and relevant resources.

Maintain changes in the owning repository. Configure callers with the actual installation path and record the tool revision when it matters for reproducing a result.
