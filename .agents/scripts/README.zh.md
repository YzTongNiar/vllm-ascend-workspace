# 工作区辅助脚本

中文 | [English](README.md)

`repo_init.py` 用于初始化源码仓库并配置个人 fork 远端。`workspace.py` 提供可独立调用的文件系统与 Git 工作树（worktree）操作。两者均使用 Python 3 和 Git；创建工作树需要 Git 支持 `git worktree add --relative-paths`。

## 仓库初始化

在工作区根目录运行 `python3 .agents/scripts/repo_init.py`。脚本会询问 GitHub 用户名，或分别输入两个 fork 的 URL / `OWNER/REPOSITORY`。请提供你已有的 fork。用户名或 `OWNER/REPOSITORY` 简写默认生成 HTTPS 地址；显式传入的 Git URL 按原样使用。

```bash
python3 .agents/scripts/repo_init.py --github-user YOUR_GITHUB_USER --no-input
python3 .agents/scripts/repo_init.py --vllm-fork OWNER/vllm --vllm-ascend-fork OWNER/vllm-ascend --no-input
```

脚本会按工作区记录的提交初始化尚未检出的 `vllm` 与 `vllm-ascend` 子模块；已有的检出、分支和本地修改会保留。脚本将各源码仓库的 `origin` 设为所选 fork，将 `upstream` 设为 `https://github.com/vllm-project/<repository>.git`，并清除单独的 push-URL 覆盖配置，使拉取与推送均指向上述远端。`.gitmodules` 保持社区上游地址。关联的源码工作树共享这些远端配置。

所选 fork 会保存在被 Git 忽略的 `workspace.json` 的 `forks.vllm` 和 `forks.vllm-ascend` 中。新建配置时若存在 `workspace.json.example` 则以其为初始模板，已有字段会保留。显式 `--*-fork` 参数优先于 `--github-user`，其次为已保存的配置。缺失配置时会交互式询问用户；传入 `--no-input` 时会在修改任何仓库前直接报错。Agent 在无法交互输入时应先向用户询问，再将结果作为参数传入。

`--root PATH` 可指定工作区路径；默认根据脚本自身位置定位工作区，与调用时的当前目录无关。进度与提示输出到 stderr，最终结果以 JSON 输出到 stdout。仓库初始化与用于创建单个任务目录的 `workspace.py task-init` 相互独立。

## 路径与配置

默认路径基准是包含本脚本的工作区根目录。即使从其他工作目录调用命令，相对目录参数和配置中的仓库路径仍以该工作区根目录为基准。`--root PATH` 可选择另一个工作区；相对的 `--root` 相对于当前调用目录解析。全局选项请放在子命令名称之前。

工作树操作接受仓库路径或 `workspace.json` 中 `repositories` 映射定义的名称。`--config PATH` 可指定相对于工作区根目录的其他配置文件。直接传入仓库路径时无需配置文件。任务与目录操作直接使用所传入的路径，不依赖该配置。

Git 工作树连接与任务软链接均使用相对路径。任务元数据中记录的路径相对于该任务目录。

## 操作说明

| 命令 | 功能说明 |
|---|---|
| `worktree-add REPOSITORY DIRECTORY --ref REF` | 添加分离头指针（detached）工作树；`--branch NAME` 可创建新分支；默认 ref 为 `HEAD` |
| `task-init DIRECTORY --title TITLE` | 创建任务目录及可编辑的 `task.json`；默认标题为目录名 |
| `worktree-remove REPOSITORY DIRECTORY` | 调用 Git 移除指定工作树及其注册信息 |
| `directory-remove DIRECTORY` | 删除指定目录；若目标为软链接，则仅删除软链接本身 |

任务初始化支持 `--records PATH` 和 `--results PATH`，用于创建目标目录及相对路径软链接。若任务元数据已存在或软链接名称已被占用，命令会报错并保留原有内容。`task.json` 中的字段可按需扩展。

两个删除命令均支持 `--dry-run` 以预览目标路径。移除工作树时，`--force` 会直接透传给 Git（可重复指定），Git 原生错误会原样返回给调用方；移除工作树仍会保留对应分支。目录删除会删除所选文件系统目录及其内容，软链接指向的目标目录保持不变。工作区根目录及其祖先目录受保护，不会被普通目录删除命令移除。

## 示例

在工作区根目录运行以下示例。若从其他目录运行，请使用 `workspace.py` 的实际路径；其参数解析基准保持不变。

```bash
python3 .agents/scripts/workspace.py --help
python3 .agents/scripts/workspace.py task-init .worktrees/demo --title demo
python3 .agents/scripts/workspace.py worktree-add vllm .worktrees/demo/vllm --ref HEAD
python3 .agents/scripts/workspace.py worktree-remove vllm .worktrees/demo/vllm --dry-run
python3 .agents/scripts/workspace.py worktree-remove vllm .worktrees/demo/vllm
python3 .agents/scripts/workspace.py directory-remove .worktrees/demo
```

初始化任务时可同时创建记录与结果软链接：

```bash
python3 .agents/scripts/workspace.py task-init .worktrees/experiment --records .vaws-local/tasks/experiment/records --results .vaws-local/tasks/experiment/runs
```

## 输出结果

命令向 stdout 输出单行 JSON 结果，向 stderr 输出执行信息。执行失败时返回非零退出码和包含错误信息的 JSON 结果；参数解析错误则输出 CLI 用法说明。执行有依赖关系的后续操作前，请先读取命令返回结果。

如需修改这些脚本，请先阅读工作区[维护指南](../../CONTRIBUTING.zh.md)，了解验证要求和文档约定。
