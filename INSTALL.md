# Installing Study Companion

[中文安装说明](INSTALL.zh.md)

Pick the edition first: `study-companion` (English) or `study-companion-zh` (Chinese). The steps below use the English one; swap the folder name for the Chinese edition.

There are two things you might install:

- **The skill folder** (or its zip), for assistants that load skills.
- **The starter prompt**, [templates/starter-prompt.en.md](templates/starter-prompt.en.md), for assistants that do not.

To get the files, download the zip for your edition from the repository's [Releases](https://github.com/quentinliu-a11y/study_assistant_skill/releases) page, or clone the repository:

```sh
git clone https://github.com/quentinliu-a11y/study_assistant_skill
```

Product menus change. If a menu named here has moved, look for the assistant's skills settings; the files to install stay the same.

## Claude Code

Copy the skill folder into your personal skills directory, or into `.claude/skills/` inside one project.

```sh
# macOS / Linux
mkdir -p ~/.claude/skills
cp -r study_assistant_skill/skills/study-companion ~/.claude/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse study_assistant_skill\skills\study-companion "$HOME\.claude\skills\"
```

Start a new session and say "Use the study companion". This is Full mode: records are kept by the local tool in a folder you choose, for example `personal/`. It needs Python 3.11 or later.

## Claude app (web and desktop)

1. Open **Customize > Skills**.
2. Click **+**, then **Create skill**, then **Upload a skill**.
3. Choose `study-companion-v<version>.zip`.
4. Make sure the skill is switched on. Skills need code execution and file creation to be enabled in your settings.

Code in the app runs in a temporary workspace, so a database written there does not carry over to your next conversation. Unless you have connected a folder on your computer, keep your progress with `handoff.md`: save the one the assistant gives you at the end and attach it next time.

## Codex CLI

Copy the skill folder into `~/.agents/skills/` for all projects, or `.agents/skills/` inside one repository.

```sh
mkdir -p ~/.agents/skills
cp -r study_assistant_skill/skills/study-companion ~/.agents/skills/
```

Restart Codex and call it with `$study-companion`. This is Full mode.

## ChatGPT

**If your account has Skills:** go to **Skills**, select **Create**, then **Upload from your computer**, and choose the release zip or the skill folder. ChatGPT reviews uploaded skills before they can be used. As in the Claude app, save `handoff.md` at the end of each session and attach it next time.

**If it does not, use a Project:**

1. Create a Project for the course and upload your course materials to it.
2. Open [templates/starter-prompt.en.md](templates/starter-prompt.en.md), copy everything below the line, and paste it into the Project's instructions.
3. At the end of each session, save the `handoff.md` the assistant writes and upload it to the Project, replacing the old one.

## DeepSeek and other plain chat assistants

1. Start a new chat.
2. Paste everything below the line in [templates/starter-prompt.en.md](templates/starter-prompt.en.md) as your first message.
3. Paste your latest `handoff.md` if you have one, then say which course you want to study.
4. At the end, copy the new `handoff.md` and the session digest the assistant writes, and save them yourself.

Repeat steps 1 to 3 for every new chat. Nothing is remembered between chats unless you paste it.

## Other agents that read `SKILL.md`

Cursor, Gemini CLI, GitHub Copilot, and others follow the same open format. Put the skill folder in the skills directory that tool documents. If the tool can run commands you get Full mode; otherwise it works like a Project.

## Check that it works

Ask: "Use the study companion. Which mode are you in, and what do you need from me?" A correct answer names Full, Project, or Chat mode and asks for your major and study level.

## Keeping local records from web sessions

If you study in a web chat but also have a Full-mode setup, save each session digest as a `.json` file and ask your Full-mode assistant to import it, or run:

```sh
python skills/study-companion/scripts/study_store.py import-session --config personal/config.json --db personal/study.sqlite3 --input personal/digest.json
```

## What has been tested

The local tool is covered by automated tests on Windows and Linux. The upload steps for the Claude app and ChatGPT follow their help pages as of November 2026 and have not been run end to end with this skill. How closely each assistant follows the starter prompt has not been measured.
