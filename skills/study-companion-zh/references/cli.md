# 命令（完整模式）

需要 Python 3.11 或更高版本。Windows 上找不到时区名时运行 `pip install tzdata`。以下路径相对本 Skill 文件夹。工具没有网络或模型调用，也不读取浏览器数据。

每条命令成功时输出 JSON 并以 0 退出。失败时输出 `Not saved: ...` 并以 2 退出，且不写入任何内容。命令的报错信息是英文，请转述给用户。

## 档案

```sh
python scripts/study_store.py profile --config personal/config.json --major "航空航天工程" --degree masters --lang zh --timezone Asia/Singapore
```

不带 `--major` 或 `--degree` 时会询问。再次运行即修改档案，课程和历史保留。

## 每日回顾

```sh
python scripts/study_store.py review pick --db personal/study.sqlite3 --config personal/config.json --course aerodynamics
python scripts/study_store.py review mark --db personal/study.sqlite3 --config personal/config.json --course aerodynamics --id separation --outcome correct --note "用户的原话"
python scripts/study_store.py review skip --db personal/study.sqlite3 --config personal/config.json --course aerodynamics
python scripts/study_store.py question add --db personal/study.sqlite3 --course aerodynamics --id separation --confusion "逆压梯度为什么会使流动分离" --prompt "逆压梯度下近壁流体会怎样？" --concept boundary-layer-separation --date 2026-11-12 --source thread-id
python scripts/study_store.py question list --db personal/study.sqlite3 --course aerodynamics
```

- `review pick`：当天已有一轮时返回 `already_started: true` 和当天的题；否则选出最多 `--limit`（默认 2）道到期题并记为已提问。用户要求加练时加 `--again`。
- `review mark` 的 `--outcome` 取 `correct|hinted|incorrect|skipped`。`correct` 必须带 `--note`。
- 对已有 ID 运行 `question add`，只需 `--date` 和 `--source` 即可追加一次出现。
- "今天"取 `--timezone` 的当前日期，其次是配置里的时区，再次是 Asia/Shanghai。`--date YYYY-MM-DD` 可覆盖。

## 保存学习问答

```sh
python scripts/study_store.py import --config personal/config.json --db personal/study.sqlite3 --input personal/turns.json
python scripts/study_store.py pending --db personal/study.sqlite3
python scripts/study_store.py commit --config personal/config.json --db personal/study.sqlite3 --input personal/update.json --expected-version 0
python scripts/study_store.py export --db personal/study.sqlite3 --config personal/config.json --course aerodynamics --out personal/exports
```

`import` 接受完整问答的 JSON 列表。只有拿得到真实消息 ID 和时间时才用它：

```json
{
  "schema_version": 1,
  "course_id": "aerodynamics",
  "session_id": "confirmed-session-1",
  "thread_id": "source-thread-id",
  "turn_id": "source-turn-id",
  "occurred_at": "2026-09-27T10:00:00+08:00",
  "user_text": "近壁流体为什么容易在逆压梯度下分离？",
  "assistant_text": "完整回答，不能用摘要代替。",
  "complete": true,
  "learning_confirmed": true,
  "is_learning": true
}
```

`occurred_at` 是提问的时间，带时区。不要编造 ID 或时间；拿不到就用下面的 `import-session`。已完成的问答不能改写；未完成的可以补全一次。

`pending` 返回四轮一批的批次和各课程版本。`pending --flush` 还返回不足四轮的尾批。

`commit` 接受一批的总结：

```json
{
  "batch_ids": [["source-thread-id", "source-turn-id"]],
  "update": {
    "course_id": "aerodynamics",
    "session_id": "confirmed-session-1",
    "events": [{
      "source_turn_ids": [["source-thread-id", "source-turn-id"]],
      "concept_ids": ["boundary-layer-separation"],
      "question": "不清楚逆压梯度如何使近壁流体减速",
      "explanation_status": "explained",
      "mastery": "unverified",
      "mastery_evidence": [],
      "links": ["adverse-pressure-gradient"],
      "correction_of": null
    }],
    "next_start": "请用户区分无滑移条件与分离判据"
  }
}
```

- 一批含一到四轮，且必须是该对话最早的未保存轮次。事件要覆盖批内每一轮。
- `mastery_evidence` 每项为 `{"source_turn_id": [thread_id, turn_id], "quote": "..."}`。引文必须出现在那条用户消息里。
- `correction_of` 填 `state --db ... --course ...` 返回的完整 `event_id`。
- `--expected-version` 是 `pending` 或 `state` 给出的课程版本。版本冲突时重新读取状态并合并，不要只改数字。
- 用相同总结重复提交同一批没有影响。对已保存的批次提交不同总结会被拒绝；请追加一条更正。

## 导入会话摘要

```sh
python scripts/study_store.py import-session --config personal/config.json --db personal/study.sqlite3 --input personal/digest.json
```

接受没有工具的助手在会话结束时写出的摘要（[格式](portable.md)）。摘要里的条目会标记为"会话摘要"保存，因为无法与原始消息核对，导出时会注明。同一份摘要导入两次不会有任何变化。未通过检查的摘要不会写入任何内容。

## 导出

`export` 写入 `<out>/<course>/`：

| 文件 | 内容 |
|---|---|
| `handoff.md` | 下次起点、尚未掌握的概念、回顾疑问及到期日。交给任何助手即可接续。 |
| `current-state.md` | 每个概念的最新事件 |
| `logs/YYYY-MM-DD.md` | 按学习当天归档的历史 |
| `recurring-questions.md`、`review-history.md` | 有了至少一条回顾疑问后才生成 |

这些文件都由数据库重建，自己的笔记请放在别的文件里。旧版本留下的手写 `recurring-questions.md` 或 `review-history.md`，第一次导出时会被改名为 `*.manual-backup.md`，不会被覆盖。Markdown 里的事件 ID 缩短为八位。`--lang` 和 `--timezone` 可覆盖配置。

请备份数据库：只有 Markdown 无法恢复原始问答。提交成功后导出失败，只需重新运行 `export`。
