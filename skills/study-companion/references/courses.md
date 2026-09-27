# 课程入口

课程配置位于用户选择的个人配置文件；不在公开 Skill 写入个人 Project ID。

1. 首次使用先收集 `profile.major` 和 `profile.degree_level`。
2. 按用户明确课程、可见 Project 绑定或专业加学习意图选择课程。
3. 从配置中的 resource_dir 读取 overview.md、knowledge-map.md，从 state_dir 读取 current-state.md；两者都相对配置文件所在目录解析。未指定 state_dir 时查找个人导出目录 exports/<course_id>/，不存在则报告尚无状态。只读本题相关来源，必要时回查原件。
4. 新课程资料不足时先列缺失来源，不把通用学科目录标成用户真实课程。

课程知识资源可随用户个人目录组织。课程间用稳定 concept_id 建立先修与关联关系；跨课程问题有主课程，其他课程只建立引用，避免重复记录同一批问答。

示例层级：学习伙伴 → 用户课程 → Aerodynamics / Mechanics / Flight Mechanics。示例不限制其他专业，也不代表 ChatGPT 自动新增原生菜单。
