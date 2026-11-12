# 学习伙伴

[English](README.md)

一个给 AI 助手用的学习 Skill。它依据你自己的课程资料教学，把你答错的内容隔一段时间再问一遍，并留下能分清"问过什么、讲过什么、你证明自己会什么"的记录。

有两个版本，规则相同：`study-companion-zh`（中文）和 `study-companion`（英文）。装一个即可。

## 按你的助手能做什么来选用法

能得到什么功能，取决于助手的能力，不取决于它是哪家的产品。每个产品的分步安装说明见 **[INSTALL.zh.md](INSTALL.zh.md)**。

| 助手 | 安装什么 | 模式 |
|---|---|---|
| Claude Code | Skill 文件夹放入 `~/.claude/skills/` | 完整模式 |
| Codex CLI | Skill 文件夹放入 `~/.agents/skills/` | 完整模式 |
| Claude 应用（网页、桌面） | 在 Customize > Skills 上传发布的压缩包 | 单次对话内为完整模式；跨对话靠 `handoff.md` |
| ChatGPT | 在 Skills 上传 Skill，或把[启动提示词](templates/starter-prompt.zh.md)粘贴进 Project | 项目模式 |
| DeepSeek 及其他普通聊天 | 把[启动提示词](templates/starter-prompt.zh.md)作为第一条消息 | 对话模式 |
| 其他读取 `SKILL.md` 的智能体 | Skill 文件夹放入该工具的 Skill 目录 | 能运行命令即为完整模式 |


完整模式下，由本地工具计数、挑选每日回顾题并排定下次回顾日期。项目模式和对话模式下，这些靠助手遵守指令完成，每次学习结束时你需要保存它给出的两段文本。你可以在不同助手之间切换：`handoff.md` 在各模式下是同一份文件。

只有完整模式有自动化测试覆盖。各家助手对启动提示词的遵守程度尚未验证，请试用后检查它生成的交接文件。

## 首次使用

告诉助手你的专业，以及是本科、硕士还是博士，然后说出课程：

> 使用学习伙伴。我的专业是____，目前是____。我想学习____，请先确认可用的课程资料，再开始学习并记录。

之后可以说：

- "开始学习并记录空气动力学。"
- "更新学习记录。"
- "把刚才答错的加入回顾疑问。"
- "今天跳过回顾。"
- "考试模式：按第 3 到 5 章出一份模拟卷。"
- "暂停记录。"／"今天学到这里，保存剩余内容。"

## 它怎样陪你学

- 每天第一次学某门课时，先问一到两道到期的回顾题。答对后下次回顾依次推到 1、3、7、14、30 天后；答错或靠提示答出，第二天再问。
- 讲解按固定顺序：输入、输出和用途；适用假设；推导；一个例子；一个检验问题。
- 听过讲解只记为"已讲解"。只有你自己的作答（引用原话）才记为掌握。
- 记录归档到学习当天，不是保存当天。

完整规则在 Skill 里：[教学](skills/study-companion-zh/references/teaching.md)、[记录](skills/study-companion-zh/references/records.md)、[回顾](skills/study-companion-zh/references/review.md)。

## 本地记录（完整模式）

需要 Python 3.11 或更高版本；Windows 上运行 `python -m pip install -r requirements.txt` 安装时区数据。命令由助手替你执行，说明见[命令](skills/study-companion-zh/references/cli.md)，也可运行 `python skills/study-companion-zh/scripts/study_store.py --help` 查看。

把档案、资料、数据库和导出文件放在 `personal/` 这类目录，本仓库默认忽略它。不要提交到公开仓库。请备份数据库：Markdown 导出可以由它重建，反过来不行。

要把项目模式或对话模式的学习并入本地记录，保存助手给出的会话摘要，然后运行 `import-session`。

### 从 0.1 升级

- 任一命令首次打开数据库时会就地升级。
- `recurring-questions.md` 和 `review-history.md` 现在由数据库生成。有了第一条疑问后首次导出时，手写的旧文件会被改名为 `*.manual-backup.md`。已有的疑问请用 `question add` 重新录入。
- 配置里的 `batch_size` 不再使用。导出采用配置里的 `timezone` 和 `language`。
- 项目指令由启动提示词取代。

## 仓库结构

```text
skills/study-companion/       英文 Skill：SKILL.md、references/、scripts/
skills/study-companion-zh/    中文 Skill，结构相同；脚本是副本
templates/                    启动提示词、配置示例、课程模板
scripts/sync.py               重新生成中文版脚本副本和启动提示词
scripts/build_release.py      每个版本生成一个压缩包
INSTALL.md、INSTALL.zh.md     各助手的安装步骤
tests/                        使用合成数据的单元测试
```

## 开发

```sh
python -m unittest discover -s tests -v
python scripts/sync.py            # 修改脚本、核心规则或 portable.md 之后运行
python scripts/build_release.py --out dist
```

发布新版本：更新 `VERSION`，合并后推送标签 `v<版本号>`，工作流会生成压缩包并附到 Release。

脚本只在 `skills/study-companion/scripts` 下修改。改规则时两个版本都要改；有一条测试检查两者结构一致。设计说明见 [generated-docs](generated-docs/README.md)。

## 许可证

[MIT](LICENSE)
