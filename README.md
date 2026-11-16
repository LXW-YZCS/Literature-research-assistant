# Literature Research Assistant

一款致力于辅助科研初学者阅读文献、制作 PPT 和讲稿、支持日常科研的 Skill。

科研助手 Skill：按任务支持文献阅读与追问、研究讨论、实验设计、学术写作、科研图表，以及论文汇报策划、PPT 和讲稿。入口为 `SKILL.md`；规则按需从 `references/` 加载，脚本位于 `scripts/`。

## 使用

将本目录作为 `literature-research-assistant` 安装到支持 Codex Skills 的环境，调用 `$literature-research-assistant` 并描述具体科研任务。阅读论文不会自动启动 PPT 制作。制作和编辑 PPT 时，默认需要相应的 WPS 前台操作能力；不同机器的软件、字体和工具可用性需要自行检查。

本仓库吸收了 [ppt-master](https://github.com/hugohe3/ppt-master) 的部分设计思路，但不包含其完整项目。仅当需要 SVG 转换等可选能力时，适配器需要单独安装兼容的 ppt-master 和 Python 环境；默认 WPS 路线不依赖运行整套 SVG 转换。上游按其自身 MIT 许可证分发。本仓库不包含本地 Python 虚拟环境、用户论文或 PPT 模板库。部分脚本依赖 Python 第三方包及其他独立 Skill；请检查实际环境，不能把文件存在等同于工具已安装或跨平台兼容。

## 范围与验证

阅读理解、图表、PPT 设计和口播质量依赖论文内容、运行工具以及人工核查。自动检查不能证明研究结论正确或排版适合现场投影。`references/validation-status.md` 记录的是特定环境和任务下的验证，不代表所有安装环境均已验证。

本项目自身尚未声明开源许可证；第三方组件适用其各自许可证。请在确定项目许可证之前勿假定整个仓库可按某个许可证再分发。

