# Task data

This directory stores task records, experiment outputs, and related files. A task can use the following organization:

```text
<task-id>/
├── task.json                  # Goal, source references, and task metadata
├── records/                   # Progress, findings, and handoff notes
└── runs/
    └── <run-id>/               # Commands, receipts, logs, metrics, and artifacts
```

For resumable work, keep a short record of the goal, completed work, evidence locations, unresolved questions, and next action. Record source revisions and commands needed to interpret an experiment, and distinguish observations from plans.

Choose record fields and run contents to suit the task. When using MindIE tools, retain their native exported records and execution receipts where useful; generate files for the operations actually performed.
