# 便携记录（项目模式和对话模式）

不能运行命令时使用。两段文本负责在不同会话、不同助手之间传递用户的进度。

<!-- portable:start -->
## 开始时

如果对话或项目文件里还没有用户最新的 `handoff.md`，请用户提供。里面有下次起点、尚未掌握的概念、回顾疑问及到期日，以及最近回顾日。最近回顾日是今天，就不要再开一轮回顾。没有交接文件时如实说明，不要编造旧疑问。

## 会话结束时，以及用户要求更新记录时

先告诉用户：对话之外尚未保存任何内容。然后输出下面两段，供用户保存。

**1. 新的 `handoff.md`，完整内容，替换旧文件：**

```markdown
# <course_id> 学习交接

## 下次起点

<一两句话：从哪里接着学>

## 尚未掌握的概念

- <concept_id>: <用户的具体缺口> (待验证 | 需要帮助)

## 待回顾的疑问

最近回顾日：<YYYY-MM-DD 或 无>

- <疑问 ID>｜<待验证 | 需要帮助 | 可独立解释 | 可独立应用>｜下次回顾：<YYYY-MM-DD 或 随时>｜<回顾短题>
```

回顾日期：每连续独立答对一次，下次回顾依次在 1、3、7、14、30 天后。提示后答出或答错，改为"需要帮助"，第二天到期。跳过的题日期不变。

**2. 一份 JSON 格式的会话摘要，供日后导入用户的本地记录：**

```json
{
  "schema_version": 1,
  "kind": "session_digest",
  "course_id": "aerodynamics",
  "date": "2026-11-12",
  "source": "当前助手或应用的名称",
  "next_start": "从哪里接着学",
  "items": [
    {
      "question": "用户的具体疑问或缺口",
      "learner_words": "用户自己的作答原话；没有作答则留空",
      "explanation_status": "explained",
      "mastery": "unverified",
      "concept_ids": ["concept-id"],
      "links": []
    }
  ],
  "open_questions": [
    {"id": "question-id", "confusion": "哪里不理解", "prompt": "回顾短题", "status": "needs_help"}
  ],
  "review_results": [
    {"id": "question-id", "outcome": "correct", "note": "用户的原话"}
  ]
}
```

`explanation_status` 取 `not_explained`、`explained` 或 `corrected`。`mastery` 取 `unverified`、`needs_help`、`can_explain` 或 `can_apply`，后两种必须填 `learner_words`。`outcome` 取 `correct`、`hinted`、`incorrect` 或 `skipped`，`correct` 必须填 `note`。`date` 是学习发生的日期。ID 由小写字母、数字和连字符组成。
<!-- portable:end -->

## 这两种模式无法保证的事

数到四轮、记得保存，都依赖助手在长对话里持续遵守指令。只有完整模式由工具强制执行。数不清时就提前保存。
