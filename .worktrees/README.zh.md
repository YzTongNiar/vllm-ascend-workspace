# 开发工作目录

中文 | [English](README.md)

本目录存放按任务工作目录组织的源码仓库工作树（worktree）。进行 vLLM 与 vLLM Ascend 开发时，每个任务目录包含该任务所需的源码工作树。

## 参考目录结构

```text
.worktrees/
└── feat-name/
    ├── AGENTS.md               # 任务入口说明、源码位置与数据位置
    ├── vllm/                   # 配套 vLLM 版本的任务工作树
    ├── vllm-ascend/            # 任务分支工作树
    ├── task.json -> ../../.vaws-local/tasks/<task-id>/task.json
    ├── records -> ../../.vaws-local/tasks/<task-id>/records/
    └── results -> ../../.vaws-local/tasks/<task-id>/runs/
```

`feat-name` 为易读的任务目录名，`<task-id>` 标识所选的任务数据目录。目录名及包含的仓库可按任务需要调整。任务目录用于聚合当前任务内容，其中的每个源码目录各自是对应源码仓库的一个 Git 工作树。

保持任务目录中的 `AGENTS.md` 简明扼要：说明任务入口、源码路径和数据路径即可。进行配套开发时，请选择与任务所用 vLLM Ascend 版本对应的 vLLM 版本；若存在 `.github/vllm-main-verified.commit`，可将其作为配套版本参考。修改代码前，请阅读所检出版本下源码仓库的 AGENTS.md 以及更贴近目标文件的相关说明。

上例中的软链接目标均相对于 `feat-name/`。辅助脚本的 `task-init` 命令可创建 `records` 和 `results` 软链接，并在任务目录本地写入 `task.json`。如需使用上例所示的 `task.json` 软链接，可将该文件放到所选持久化目录后创建相对软链接。

## Git 操作说明

同一源码仓库的多个工作树共享提交历史、分支和远端配置，而每个工作树拥有各自独立的工作区文件、HEAD 和暂存区（index）。

移除 Git 工作树会同时清理检出目录及其在 Git 中的工作树注册信息；普通目录删除仅操作文件系统内容。请根据被删除对象的类型选择相应操作。
