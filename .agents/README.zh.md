# Agent 共享资源

中文 | [English](README.md)

本目录存放共享辅助脚本、示例以及项目级 agent 资源。请根据当前任务从对应入口开始查阅。

| 入口 | 用途 | 适用场景 |
|---|---|---|
| [scripts/](scripts/README.zh.md) | 可独立调用的工作区操作脚本 | 创建工作树、初始化任务或清理目录 |
| [examples/](examples/README.zh.md) | 可按需调整的示例 | 选择任务记录的初始结构 |

可选技能（skill）可按所选客户端的发现机制安装或链接到 `skills/<skill-name>/` 下。技能包包含带有 `name` 和 `description` YAML 头部的 `SKILL.md`，还可包含 `scripts/`、`references/` 和 `assets/`。根据描述选择所需技能后，再阅读其说明及当前任务所需的资源。

这些路径仅用于组织文件；指令和技能的实际加载取决于客户端、其配置以及启动目录。从子模块或任务工作树启动 agent 时，请核对实际发现的指令和技能，必要时使用显式文件引用或客户端支持的配置方式提供目标资源。

如需修改共享 agent 资源，请阅读工作区[维护指南](../CONTRIBUTING.zh.md)。
