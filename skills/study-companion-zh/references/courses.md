# 课程与个人数据

## 配置文件

用户的配置是放在本 Skill 之外的一个 JSON 文件，例如 `personal/config.json`：

```json
{
  "schema_version": 1,
  "profile": {"major": "航空航天工程", "degree_level": "masters"},
  "language": "zh",
  "timezone": "Asia/Singapore",
  "courses": [
    {"course_id": "aerodynamics", "resource_dir": "courses/aerodynamics", "state_dir": "courses/aerodynamics"}
  ]
}
```

- `degree_level` 取 `undergraduate`、`masters`、`doctoral` 或 `postgraduate`。
- `language`（`en` 或 `zh`）决定提示语和导出 Markdown 的语言。`timezone` 是 IANA 时区名，决定"今天"是哪一天。
- `course_id` 由小写字母、数字和连字符组成，字母开头，最长 64 个字符。
- 路径相对配置文件所在目录。`resource_dir` 放 `overview.md`、`knowledge-map.md` 和可选的课程规则文件。`state_dir` 接收导出的记录；未设置时查找 `exports/<course_id>/`，没有状态就如实报告。

## 选择课程

使用用户指明的课程，或当前工作区明确对应的课程。消息里出现专业术语，不代表用户正在学那门课。新课程资料不足时，先列出缺什么。

会话开始时，读该课程的 `overview.md` 和 `knowledge-map.md`，再读 `handoff.md`（或 `current-state.md` 与最新的日期日志）。只读当前问题需要的来源。

## 课程专属规则

某一门课特有的规则，比如它的符号、常见陷阱、教师对某个量的定义，写在该课程 `resource_dir` 里的规则文件中，开始这门课时读取。它是对本 Skill 的补充，不能推翻核心规则。

## 保密

档案、课程资料、疑问、日志和数据库都是个人数据。把它们放在本 Skill 之外、任何公开仓库之外的目录。公开 GitHub 仓库里的文件夹不能单独设为私密，所以同步记录前先确认目标仓库是私有的。
