# Persistent local data

This directory stores local notes, temporary data, and results to retain. The following layout is a reference; create the directories useful for your work and adapt their contents as needed.

```text
.vaws-local/
├── tasks/
│   └── <task-id>/
│       ├── task.json           # Task metadata
│       ├── records/            # Development notes and evidence summaries
│       └── runs/
│           └── <run-id>/       # Outputs from one experiment or execution
├── machines/                  # Local machine registrations and connection references
├── shared/                    # Material and datasets shared across tasks
├── cache/                     # Rebuildable or downloadable cached data
└── archives/                  # Retained task data, snapshots, and historical outputs
```

Choose formats and retention according to the data's purpose. Keep reusable shared data distinct from per-run outputs, and identify cached data that can be regenerated. The shared directory documentation and ignore rules are versioned; personal contents remain local.
