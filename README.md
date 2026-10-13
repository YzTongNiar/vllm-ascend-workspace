# vLLM Ascend workspace

简体中文 | [English](README.en.md)

可按个人习惯组合的本地开发脚手架。根仓库维护文档、配置模板、agent 配置和辅助脚本，并通过子模块引用 vLLM 与 vLLM Ascend。

## 目录结构

```text
.
├── vllm/                    # vLLM 源码子模块，便于人工查验
├── vllm-ascend/             # vLLM Ascend 源码子模块，便于人工查验
├── .worktrees/              # 开发工作树与任务工作目录
├── .vaws-local/             # 本地事项、临时数据与持久化结果
├── tools/                   # 自行安装和维护的独立工具、技能仓库
├── .agents/                 # 共享 agent 配置、辅助脚本与示例
│   ├── scripts/             # 工作树创建、任务初始化和目录清理脚本
│   └── examples/            # 可按需修改的任务示例
├── .claude/                 # Claude 项目配置与规则入口
├── .codex/                  # Codex 项目配置模板
├── .cursor/                 # Cursor 项目配置与规则入口
├── .trae/                   # Trae 项目配置与规则入口
├── .gitignore               # 根仓库的文件追踪范围
├── .gitmodules              # 两个源码子模块的上游地址
├── workspace.json.example   # 个人工作区配置模板
├── AGENTS.md                # Agent 协作说明
├── README.md                # 中文说明，默认入口
└── README.en.md             # 英文说明
```

## 使用

按需初始化源码：

```bash
git submodule update --init vllm vllm-ascend
cp workspace.json.example workspace.json
```

`workspace.json` 保存个人配置。`repositories` 可为脚本中的仓库参数配置别名；配置路径相对于工作区根目录解析。`tools` 可登记自行安装的工具路径。

根目录源码可用于查验。下面的命令演示创建一个开发目录，并为两个源码仓库添加工作树；ref 和分支名按当前任务选择。

```bash
python3 .agents/scripts/workspace.py task-init .worktrees/demo --title demo
python3 .agents/scripts/workspace.py worktree-add vllm-ascend .worktrees/demo/vllm-ascend --ref HEAD --branch codex/demo
python3 .agents/scripts/workspace.py worktree-add vllm .worktrees/demo/vllm --ref HEAD
```

脚本以自身所在工作区为路径基准，可从任意当前目录调用；`--root` 可指定另一个工作区。源码版本由调用参数选定。Ascend 配套开发可参考所选版本的 `.github/vllm-main-verified.commit` 选择 vLLM ref。

辅助命令及选项见 [.agents/scripts/README.md](.agents/scripts/README.md)。任务示例见 [.agents/examples/task](.agents/examples/task)。工具和技能可自行放入 `tools/`，各自维护其 Git 仓库。
