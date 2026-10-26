# 本地存储数据合同（版本 1）

需要 Python 3.11+；Windows 使用 IANA 时区时安装 tzdata。脚本路径相对本 Skill 根目录。它没有网络或模型调用，不会读取浏览器数据库、自动监听 ChatGPT 或推送 GitHub。

## 先建立档案

```sh
python scripts/study_store.py profile --config personal/config.json
```

程序询问专业和本科/研究生阶段。也可用 `--major "航空航天工程" --degree masters`；再次指定参数修改档案，保留课程和历史记录。阶段可用 undergraduate / postgraduate / masters / doctoral。个人目录应放在发布包之外并被版本控制忽略。

## 输入轮次

`import` 的 JSON 是对象列表。每项必填：

```json
{
  "schema_version": 1,
  "course_id": "aerodynamics",
  "session_id": "confirmed-session-1",
  "thread_id": "source-thread-id",
  "turn_id": "source-turn-id",
  "occurred_at": "2026-09-27T10:00:00+08:00",
  "user_text": "近壁流体为什么容易在逆压梯度下分离？",
  "assistant_text": "从边界层动量与压力梯度解释，并提出理解检验。",
  "complete": true,
  "learning_confirmed": true,
  "is_learning": true
}
```

此例为合成数据。实际导入必须保留完整问答，不能用摘要代替 assistant_text。`occurred_at` 为可验证的原问题时间，不是导入时间。真实 ID 不存在时不要用当前序号伪造稳定身份。revision_hash 由脚本按内容生成；可省略，若提供必须一致。

course_id 仅小写字母开头，后接字母、数字、连字符，最长 64 字符，排除 Windows 保留名。课程/会话标识和学习确认由助手结合实际用户意图提供，不由脚本猜测。脚本拒绝非法输入，但不能证明外部输入真实。

```sh
python scripts/study_store.py import --config personal/config.json --db personal/study.sqlite3 --input personal/turns.json
python scripts/study_store.py pending --db personal/study.sqlite3
```

pending 返回四轮批次和 course_versions；`--flush` 返回不足四轮的余量，供手动更新和结束学习。需要合并其他对话状态时用 `state --db ... --course aerodynamics`。已完成消息改写会报冲突；未完成快照仅允许同问题同身份的最终回答补全。

## 总结与提交

由学习助手根据原问答生成总结，不使用额外模型请求。提交文件为：

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
      "links": ["adverse-pressure-gradient", "wall-shear"],
      "correction_of": null
    }],
    "next_start": "请用户区分无滑移条件与分离判据"
  }
}
```

每批 1–4 轮；短批代表手动保存，必须处理该会话最早尚未处理的轮次。事件覆盖全批，引用只限本批。explanation_status 为 not_explained / explained / corrected；mastery 为 unverified / needs_help / can_explain / can_apply。

后两种掌握状态必须提供 `mastery_evidence` 对象列表：每项 `source_turn_id: [thread_id,turn_id]` 与 `quote: 用户原话`。程序检查原话确实出现在用户消息中；是否足以证明掌握仍需教学判断。不要把问题原话、简短认可或助手解释当成掌握证据。

`correction_of` 可以指向 `state` 返回的旧 event_id，只能指向同课程已有事件；保留原事件。版本冲突时先重新读取课程状态再总结，不盲目改 expected_version。

```sh
python scripts/study_store.py commit --config personal/config.json --db personal/study.sqlite3 --input personal/update.json --expected-version 0
python scripts/study_store.py export --db personal/study.sqlite3 --course aerodynamics --out personal/exports --timezone Asia/Shanghai
```

返回输出路径后回读确认。写入失败不推进处理位置；相同批次和相同摘要重复提交返回原版本，不重复插入。不同摘要不能覆盖已处理批次。数据库已经保存但导出失败时，仅重试 export。

导出目录按课程分组，含 current-state.md 与 logs/YYYY-MM-DD.md；使用原轮次日期。向网页提供最新 current-state.md 后验证读取，不把本地文件存在当作网页同步成功。

## 独立维护的复习 Markdown

`recurring-questions.md` 和 `review-history.md` 放在配置的课程 `resource_dir`，由助手按 [每日回顾规则](recurring-review.md) 直接读写。它们不属于版本 1 JSON 字段，不向 commit 输入添加未支持字段；CLI 不负责语义合并、每日选题或问答触发。

保存完整学习问答仍沿用上述数据库流程；随后在四轮／手动保存时同步维护疑问清单与作答结果。提问或跳过标记及时写入 review-history.md，避免同日跨对话重复。两份文件需单独备份并同步到私有仓库；导出不会刷新它们，也不能代替其保存成功检查。
