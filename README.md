# study_assistant_skill · 学习伙伴

一个按专业与学习阶段组织课程的学习 Skill，附带本地增量记录工具。

[生成文档归档](generated-docs/README.md)只保存通用设计方案和实施计划。个人课程笔记、学习状态及日志应放在独立私有仓库，不能通过公开仓库的文件夹权限保护。

**[从首次使用入口开始](START_HERE.md)**：先告诉助手你的专业，以及本科或研究生阶段。以后可说“修改学习资料”。已提供的项目不重复询问。

## 用在 ChatGPT 网页版

继续在原有课程 Project 学习。把 [项目指令](templates/project-instructions.md) 的内容加入该 Project 的指令，开始时说“使用学习伙伴，开始学习并记录”。先完成专业和学习阶段信息，然后选择课程资料。

当前网页模式是**对话内整理 + 手动同步**：每四轮整理新增疑问、知识联系和掌握证据；“更新学习记录”或结束学习时整理剩余内容。没有实际存储工具的网页对话不能自动写入本机或 GitHub。将最新学习状态提供给下一次对话，才能验证持续使用。

每天首次开始一门课程时，先从 `recurring-questions.md` 中选择 1–2 个反复出现或仍未理解的问题，等用户作答后再反馈、继续。`review-history.md` 保存当天提问、跳过及作答情况，避免同日重复启动。两份文件由助手独立维护；本地 CLI 不自动生成，网页使用时需提供最新副本。规则见 [反复疑问与每日回顾](skills/study-companion/references/recurring-review.md)。

这个仓库和 ZIP 不是后台监听服务。上传 GitHub 不会自动将 Skill 安装到 ChatGPT、修改 Project Sources，也不会跨所有网页对话自动保存。

## Skill 的组织

```text
skills/study-companion/
  SKILL.md                 总入口与首次使用
  references/              课程路由、学习协议、数据格式
  scripts/study_store.py   本地记录入口
templates/                 个人配置、课程与网页项目指令
```

总入口按需读取课程资料，支持不同专业。课程目录可作为逻辑“二级菜单”，没有新增 ChatGPT 原生菜单。使用支持本地 Skill 的环境时，将 `skills/study-companion` 文件夹放入该环境配置的 Skill 目录；Codex 的个人目录通常为 `~/.codex/skills/`，按所在环境刷新 Skill 列表后调用 `$study-companion`。

## 本地记录工具

Python 3.11+。如系统没有 IANA 时区数据库（Windows 常见），安装依赖：

```sh
python -m pip install -r requirements.txt
python skills/study-companion/scripts/study_store.py profile --config personal/config.json
```

首次命令会询问专业和本科/研究生阶段。修改例子：

```sh
python skills/study-companion/scripts/study_store.py profile --config personal/config.json --major "机械工程" --degree masters
```

保存流程由有文件权限的学习助手执行；无需用户手写摘要 JSON，也不额外调用模型 API。完整合同和可执行例子见 [数据格式](skills/study-companion/references/data-contract.md)。

```sh
python skills/study-companion/scripts/study_store.py import --config personal/config.json --db personal/study.sqlite3 --input personal/turns.json
python skills/study-companion/scripts/study_store.py pending --db personal/study.sqlite3
python skills/study-companion/scripts/study_store.py commit --config personal/config.json --db personal/study.sqlite3 --input personal/update.json --expected-version 0
python skills/study-companion/scripts/study_store.py export --db personal/study.sqlite3 --course aerodynamics --out personal/exports --timezone Asia/Shanghai
```

`pending --flush` 包含不足四轮的余量。`state --db ... --course ...` 获取课程版本与历史；并发冲突时重新读取并合并。命令需要实际准备好的输入文件，样例命令不会自动读取网页或下载课程。

导出得到课程的 `current-state.md` 和 `logs/YYYY-MM-DD.md`。成功保存才推进计数；重复导入/提交不重复记录。保存成功但导出失败时重试 export。备份整个个人目录；工具生成的 Markdown 可以从数据库重建，独立维护的疑问清单、回顾历史和人工笔记需要另行保留。仅保留 Markdown 不能恢复原始问答和检查点。

同一课程的导出会串行执行，避免旧状态覆盖新状态。导出目录中的隐藏清单记录工具生成的日志；切换时区时，只清理清单内已过期且未被修改的日期日志。若旧日志含手工修改，工具会停止并提示先移走笔记。请将手工笔记另存文件，生成的当前状态与仍有效的日期日志会在重建时覆盖。

## 学习规则

- Lecture 定范围，Textbook 补解释，Tutorial 与明确考试资料支持重点判断。
- 每轮 = 一次学习提问和完整回答；闲聊、配置、工具调用和不完整回答不计数。
- 按课程、会话和对话独立计数；多门课程不混算。
- “已讲解”不等于“已掌握”。独立作答提供证据；学历和“懂了”不是证据。
- 反复疑问按独立来源去重，相关追问与确认复发分开；每日回顾先问后答，允许跳过，未作答不当作答错。
- 知识地图保存先修关系与来源。明确分值、题目频率和推测优先级分开记录。
- 日志按原始消息日期归档；缺少可信原始时间或稳定 ID 的采集文件不能直接导入。

## 数据与发布

个人资料、项目绑定、原始教材、问答、数据库和学习日志放在 `personal/`，默认被 Git 忽略。通用 Skill 不含任何个人专业/学历默认值。公开包只包含明确列出的 Skill 文件、模板、依赖说明和本 README。

配置的 `courses` 项使用 `course_id`、`project_ids`、`resource_dir`，可另设 `state_dir` 指向导出状态目录；路径相对配置文件目录解析。课程资料不存在时先盘点和建课，不假装已读取。

## 开发验证

```sh
python -m unittest discover -s tests -v
python scripts/build_release.py --out dist
```

测试使用合成数据，覆盖首次填写、四轮计数、重复输入、失败回滚、并发版本冲突、跨日归档和发布隔离。真实网页后台自动更新尚未验证；不在已通过的本地测试范围内。
