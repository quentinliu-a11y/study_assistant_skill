# 安装学习伙伴

[English](INSTALL.md)

先选版本：`study-companion-zh`（中文）或 `study-companion`（英文）。下面以中文版为例，装英文版时把文件夹名换掉即可。

可能要安装的东西有两种：

- **Skill 文件夹**（或它的压缩包），给能加载 Skill 的助手用。
- **启动提示词** [templates/starter-prompt.zh.md](templates/starter-prompt.zh.md)，给不能加载 Skill 的助手用。

获取文件：到仓库的 [Releases](https://github.com/quentinliu-a11y/study_assistant_skill/releases) 页面下载对应版本的压缩包，或者克隆仓库：

```sh
git clone https://github.com/quentinliu-a11y/study_assistant_skill
```

各产品的菜单会变。如果这里写的菜单找不到了，请找该助手的 Skill 设置；要安装的文件不变。

## Claude Code

把 Skill 文件夹复制到个人 Skill 目录，或某个项目里的 `.claude/skills/`。

```sh
# macOS / Linux
mkdir -p ~/.claude/skills
cp -r study_assistant_skill/skills/study-companion-zh ~/.claude/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse study_assistant_skill\skills\study-companion-zh "$HOME\.claude\skills\"
```

新开一个会话，说"使用学习伙伴"。这是完整模式：记录由本地工具保存在你指定的目录，例如 `personal/`。需要 Python 3.11 或更高版本。

## Claude 应用（网页版和桌面版）

1. 打开 **Customize > Skills**。
2. 点 **+**，再点 **Create skill**，然后选 **Upload a skill**。
3. 选择 `study-companion-zh-v<版本号>.zip`。
4. 确认该 Skill 已开启。Skill 需要在设置里启用代码执行和文件创建。

应用里的代码在临时工作区运行，写在那里的数据库不会带到下一次对话。除非你连接了电脑上的文件夹，否则请用 `handoff.md` 保存进度：结束时保存助手给出的那份，下次开始时上传。

## Codex CLI

把 Skill 文件夹复制到 `~/.agents/skills/`（所有项目可用），或某个仓库里的 `.agents/skills/`。

```sh
mkdir -p ~/.agents/skills
cp -r study_assistant_skill/skills/study-companion-zh ~/.agents/skills/
```

重启 Codex，用 `$study-companion-zh` 调用。这是完整模式。

## ChatGPT

**账号有 Skills 功能时：** 进入 **Skills**，选 **Create**，再选 **Upload from your computer**，选择发布的压缩包或 Skill 文件夹。ChatGPT 会先审核上传的 Skill。和 Claude 应用一样，每次结束时保存 `handoff.md`，下次上传。

**没有该功能时，用 Project：**

1. 为这门课建一个 Project，把课程资料上传进去。
2. 打开 [templates/starter-prompt.zh.md](templates/starter-prompt.zh.md)，复制分隔线以下的全部内容，粘贴到 Project 的指令里。
3. 每次学习结束，保存助手写出的 `handoff.md` 并上传到 Project，替换旧的那份。

## DeepSeek 及其他普通聊天助手

1. 新开一个对话。
2. 把 [templates/starter-prompt.zh.md](templates/starter-prompt.zh.md) 分隔线以下的全部内容作为第一条消息发出。
3. 如果有最新的 `handoff.md`，接着粘贴它，然后说你要学哪门课。
4. 结束时，复制助手写出的新 `handoff.md` 和会话摘要，自己保存好。

每次新对话都重复第 1 到 3 步。不粘贴的内容，对话之间不会被记住。

## 其他读取 `SKILL.md` 的智能体

Cursor、Gemini CLI、GitHub Copilot 等采用同一种开放格式。把 Skill 文件夹放进该工具文档说明的 Skill 目录即可。工具能运行命令就是完整模式，否则按项目模式使用。

## 检查是否装好

问一句："使用学习伙伴。你现在是哪种模式，需要我提供什么？"正确的回答会说出完整、项目或对话模式之一，并询问你的专业和学习阶段。

## 把网页对话的学习并入本地记录

如果你在网页对话里学习，同时也有完整模式的环境，把每次的会话摘要存成 `.json` 文件，让完整模式的助手导入，或者运行：

```sh
python skills/study-companion-zh/scripts/study_store.py import-session --config personal/config.json --db personal/study.sqlite3 --input personal/digest.json
```

## 哪些经过了测试

本地工具有自动化测试，覆盖 Windows 和 Linux。Claude 应用和 ChatGPT 的上传步骤依据其 2026 年 11 月的帮助页面编写，没有用本 Skill 完整实测过。各助手对启动提示词的遵守程度没有测量过。
