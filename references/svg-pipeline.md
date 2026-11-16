# SVG 制稿与原生 PPTX

本文件只用于用户在当前任务明确指定后台SVG整稿转换。2026-10-31用户要求默认前台WPS可视化逐页编辑，取代2026-10-30的长期后台路线授权。保留转换器技术能力，不默认调用export生成整套PPT。独立SVG素材可以后台准备；向演示中插入、布局与修改在WPS当前页执行。前台规则见visible-authoring.md。

## 本地后端

该路线需要单独安装可选的 [ppt-master](https://github.com/hugohe3/ppt-master) 后端到 `vendor/ppt-master`，并按上游许可证保留署名。本仓库不分发上游项目；此前使用的固定提交为 `5e8856be0da8e6bc85c4aa28acc614478f7b7137`。通过 `scripts/ppt_backend.py` 调用，依赖 `.runtime/Scripts/python.exe` 及相应依赖；未安装时不可使用转换能力。更换版本后应重新验证，禁止绕过上游检查。

先使用各子命令`--help`确认参数：
```
python <skill>/scripts/ppt_backend.py integrity
python <skill>/scripts/ppt_backend.py check -- --help
python <skill>/scripts/ppt_backend.py export -- --help
```

## 制作顺序

1. 按slide-design.md形成内容与设计记录，将本次工程置于任务work目录。
2. 编写`svg_output/01_*.svg`等有序页面。先读取`../vendor/ppt-master/references/shared-standards-core.md`和`../vendor/ppt-master/references/executor-base.md`（相对本文件目录），公式、图表、图片等再读相应触发模块。上游有独立SVG语法契约，不将任意浏览器SVG视为可转换。
3. 普通文本使用text/tspan，结构图使用原生形状与连线；源数据、图表和图片单独保存并记录出处。预览检查代表页后制作其余页面。
4. 运行后端check的final阶段；修复错误并重新检查。新稿可用上游Quick技术模式：它省去上游交互确认，不省去本地设计、事实核查与视觉检查。
5. 仅获当次明确后台转换授权后，使用export的`--explicit-background --quick-generate --no-notes`输出PPTX（用户要求讲稿时按上游规则提供已完成的讲稿）。必须保留当前SVG对应的最终质量报告。不要使用危险兼容选项或绕过校验。
6. 在可见WPS打开转换后的目标文件，检查实际字体、公式、图表、图片与分页，导出预览核对。仅操作本次目标；不关闭无关或未保存文件。抽查文本和形状独立编辑性，不能以ZIP结构正常代替应用验证。

编辑SVG后重新检查和导出；直接在WPS改过的页面不能被旧SVG无提示覆盖。续作先确定当前权威版本。

## 能力与实测

转换器提供上游已实现的原生DrawingML路径；特定效果、公式、图表和母版需对应语法与依赖，并逐项验证。本地可用性以`validation-status.md`记录为准。整套视觉质量仍依赖内容组织、模板学习和最终审阅，不以使用同一转换器宣称所有效果已等同上游。

块公式若需要后续SVG往返，优先放在页面根级语义模块；普通组合内的块公式可能显示正常但不能反向重建。先查看导入报告，不能将预览正确等同于可逆编辑。
