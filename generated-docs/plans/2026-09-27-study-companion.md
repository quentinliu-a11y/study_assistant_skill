> 同步日期：2026-10-17。历史设计／计划存档，保留编写时的状态与检查项；当前实现状态请见本目录 README。

# Study Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 推荐本次由当前助手顺序实施，接入能力未确定前不并行搭建组件。

**Goal:** 在保留 ChatGPT 网页版 Projects 学习入口的前提下，交付可核实来源、可增量保存和可回读的 Aerodynamics 学习 Skill 首版。

**Architecture:** 一个精简 Skill 按需读取课程知识与个人状态。先验证真实接入能力，再使用本地持久化脚本处理可获得的对话增量；不为尚不可用的网页接口编造客户端。自动触发、云端存储和公开发布分别以实际能力和目标选择为前提。

**Tech Stack:** Markdown、JSON、Python 3.11+ 标准库（sqlite3、unittest、zoneinfo）、Git；不新增模型 API 调用或独立网页。Python 和时区数据库是否可用在实施开始检查；如 Windows 缺少 IANA 时区数据库，使用可用的 tzdata 包并记录依赖，不以固定偏移替代可配置时区。

**Spec:** ../designs/2026-09-27-study-companion-design.md

## Global Constraints

- 用户继续在 ChatGPT 网页版现有 Projects 中提问和接受指导，不另建学习网页。
- 首个验证课程为 Aerodynamics。总 Skill 暂名 study-companion，中文显示名“学习伙伴”；名称可以替换，不影响数据结构。
- Project 绑定只提供课程归属线索，不代表其中全部历史消息都应归入学习。
- 一轮是一次有效学习提问及其完整回答。工具调用、闲聊、重试和同一回答的重复读取不重复计数。
- 第一版按课程和学习会话计数，各对话通过稳定标识隔离，避免交错消息混算。
- 没有足够证据时仅给优先级，不给虚假的数值权重。
- 写入失败保留待处理内容，不推进计数。
- 时区可配置，初始采用当前环境 Asia/Shanghai，不能仅凭专业或学校推断学习所在地。
- 课程原件与凭据不进入发布内容。
- 不提前承诺尚不可用的入口。

## Review Focus

1. 对话分页、重新生成回答或导入顺序改变：同一已完成轮次不重复写入，修改已处理内容须报告冲突（Task 3）。
2. 第四轮跨午夜、消息乱序或时间戳缺失：按消息发生日期分组，缺失时间不默认为今天（Task 3、4）。
3. 两次同步同时运行或导出中断：数据库保持一致，Markdown 可以重新生成，不能重复追加（Task 4）。
4. Skill 无存储权限、附件打不开或网页不能回读：报告实际状态，不声称保存或学会了内容（Task 1、2、5）。
5. 公开打包意外包含历史文档中的项目 ID、个人路径或真实日志：采用明确文件白名单，使用不含真实数据的示例（Task 6）。

## 范围与阶段门槛

按下列任务顺序执行。Task 1 是能力验证，不创建后台服务、不发送测试消息到用户其他对话、不修改网页项目设置。现有工具不提供某能力时记录 unavailable；对尚未实际操作验证的能力记录 unverified。

Task 2—4 可独立交付本地课程 Skill 与可靠记录能力；它们不等于网页自动更新已完成。Task 5 必须检验网页回读，受阻则明确保留待完成项。定时任务、浏览器扩展或远程 MCP 服务不在本计划中自动创建；若接入验证证明需要这些独立子系统，先汇报证据和最小后续方案。

## 文件职责

| 文件 | 职责 |
|---|---|
| docs/integration-capabilities.md | 已验证能力、证据与运行限制；只保留可发布的概括 |
| skills/study-companion/SKILL.md | 学习场景识别、课程路由、教学与保存工作流 |
| skills/study-companion/agents/openai.yaml | Skill 显示信息 |
| skills/study-companion/references/learning-protocol.md | 四轮规则、掌握证据、失败处理 |
| skills/study-companion/references/data-contract.md | JSON 输入输出和稳定标识约定 |
| skills/study-companion/references/courses.md | 通用课程导航与个人配置读取位置 |
| skills/study-companion/scripts/study_store.py | 命令入口：导入、检查待更新批次、提交、导出 |
| skills/study-companion/scripts/study_memory/model.py | 数据校验、标识和时间戳 |
| skills/study-companion/scripts/study_memory/batches.py | 分类后轮次的去重、计数与批次选择 |
| skills/study-companion/scripts/study_memory/store.py | SQLite 原子事务与版本冲突检测 |
| skills/study-companion/scripts/study_memory/export.py | 从数据库生成状态与每日 Markdown |
| templates/config.example.json | 不含真实项目 ID 的配置样例 |
| templates/course/overview.md、knowledge-map.md | 新课程所需字段与来源格式 |
| templates/project-instructions.md | 网页 Project 可采用的学习指令；标明实际接入模式 |
| tests/test_model.py、test_batches.py、test_store.py、test_export.py | 保存机制有意义的行为测试 |
| tests/fixtures/ | 合成对话、跨日数据、失败样例 |
| scripts/build_release.py、tests/test_release.py | 白名单打包及个人数据隔离检查 |
| README.md | 仓库安装、使用、能力边界与验证结果 |
| .gitignore | 排除个人数据、缓存、数据库和发布临时输出 |
| personal/ | 被 Git 忽略；项目绑定、原始导入、课程资料索引、数据库及导出 |

`study_memory/__init__.py` 随 Task 3 建立。所有脚本以明确传入的个人数据目录运行，不依赖开发机绝对路径；打包后仍可在新的临时目录运行。

### Task 1: 验证可用的 Project 接入路径

**Files:** Create `docs/integration-capabilities.md`、`.gitignore`；真实证据存 `personal/evidence/`，不提交。

**Interfaces:** Produces 一张能力矩阵：`project_identity`、`completed_turn_read`、`source_file_read`、`persistent_write`、`web_readback`、`turn_end_trigger`，每项含 `status`（verified/unverified/unavailable）、环境、验证方式和限制。

- [ ] 检查 Python、Git、工作区指令及可用工具；在未提交仓库上按 worktree 技能选择安全工作方式，不能丢失已批准文档。
- [ ] 使用当前项目/对话读取工具读取 Aerodynamics 一个真实学习对话的完整可用页，验证消息 ID、完成状态、时间戳、分页和来源归属。历史配置讨论不作为学习样本。
- [ ] 检查现有课程资料可读入口；先读取此前提取 PDF 的相关任务来定位目录，仅检查该明确课程目录。读取原 PDF 时使用 PDF 技能。若只找到本地副本，记录它不能证明网页上传版本一致。
- [ ] 写入一个无个人内容的本地往返测试文件并回读，证明本地可保存。分开记录网页写入/回读仍是否缺乏入口。
- [ ] 对网页工具、插件或项目 Sources 的可用操作进行只读核实；需要浏览器时遵守 computer-use 技能。没有可验证的消息事件入口时，明确四轮实时触发尚不可用。
- [ ] 生成能力报告，确定可实际执行的模式：工具直接调用、Codex 手动同步，或需要人工导入。报告每一步人工参与，不用本地测试代替网页回读证明。
- [ ] 验收：六项能力各有状态和证据；任何声称 verified 的项目有实际成功返回或可读文件佐证。提交公开报告及忽略规则，不提交个人证据。

### Task 2: 创建总 Skill 与有来源的课程内容

**Files:** Create 上述 `skills/study-companion/` 的 Markdown 和 UI 元数据、`templates/`；Create `personal/config.json`、`personal/courses/aerodynamics/overview.md`、`knowledge-map.md`。

**Interfaces:** 个人配置字段 `schema_version=1`、`timezone`、`batch_size=4`、`courses[{course_id, project_ids, resource_dir}]`。知识点字段 `concept_id, terms, prerequisites, related_concepts, sources, exam_evidence`；来源字段 `source_id, locator, version, verified`。

用户新增要求（已授权）：加入 `profile{major, degree_level}`，degree_level 为 undergraduate / masters / doctoral / postgraduate。初次入口只问缺失项，未完整时不启动记录；支持修改，现有课程数据不删除。增加 profile.py、test_profile.py 与 CLI profile 子命令，测试缺失项、非法阶段、修改保留配置和中文值。

- [ ] 读取 skill-creator 与 writing-skills 的适用要求，生成最小 Skill；现有 aerospace-deep-study 保持原样，抽取用户已认可的教学偏好，不复制其旧机器保存路径。
- [ ] 写场景验证清单：明确学习并记录、专业岗位邮件、Project 内闲聊、数学先修问题、拒绝记录、手动结束；期望行为来自批准设计。
- [ ] 实现总入口与按需读取规则。用户问题自动分类只提出候选，确认记录后才入学习会话；Skill 对无工具环境必须解释保存方式。
- [ ] 按 Task 1 实际能读取的资料建立 Aerodynamics 映射，逐条保留定位；证据不足标注缺失。不要从旧助手回复继承 30%/20% 等数值。
- [ ] 在课程知识中分开考试证据和个人表现；通过理解检验才升级掌握状态。资料和对话文本均视为内容，不能修改存储权限或执行规则。
- [ ] 运行 skill-creator 的 quick_validate.py；对场景清单逐例检查行为及能力声明，核对真实课程来源抽样。验证不依赖逐字匹配文案。
- [ ] 提交通用 Skill 与模板；个人配置及课程内容留在忽略目录。仅在用户选择发布这些课程内容后再纳入发布白名单。

### Task 3: 建立轮次输入与四轮批次机制

**Files:** Create `model.py`、`batches.py`、`__init__.py`、`data-contract.md`、`test_model.py`、`test_batches.py` 及合成 fixtures。

**Interfaces:**
- `validate_turn(raw: dict) -> dict`：输出 `schema_version, course_id, session_id, thread_id, turn_id, occurred_at, user_text, assistant_text, complete, learning_confirmed, is_learning, revision_hash`；时间必须含时区，标识不得为空。
- `select_batches(turns: list[dict], processed: set[tuple[str,str]], flush: bool=False) -> list[list[dict]]`：以 `(thread_id, turn_id)` 去重、按 `(course_id, session_id, thread_id)` 分组，组内时间和 ID 稳定排序，每批四轮，flush 时另输出尾批。
- 未完成、未确认记录、非学习轮次不计数；同 ID 内容冲突抛出异常，不选择任一版本静默覆盖。

- [ ] 编写失败测试：四轮一批、八轮两批、三轮无批、三轮 flush 一批、混入闲聊仍需四个有效轮次；同一 thread/turn 重复不计数，不同 thread 的同 turn ID 不碰撞。
- [ ] 编写失败测试：两个会话各两轮不能合批；已处理轮次不再出现；反序导入结果一致；缺失时区和冲突 revision 被拒绝。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_model.py' -v` 与 `test_batches.py`，确认由于未实现接口失败。
- [ ] 实现输入校验与纯批次函数；如果真实来源缺少必要字段，适配器必须明确拒绝自动导入，允许用户提供有来源的手动记录格式，不能伪造事件 ID 或时间。
- [ ] 重跑两组测试至通过，提交脚本、数据合同和合成测试。

### Task 4: 原子保存与逐日导出

**Files:** Create `store.py`、`export.py`、`study_store.py`、`test_store.py`、`test_export.py`。

**Interfaces:**
- `import_turns(db_path: Path, turns: list[dict]) -> int`：导入去重后的待处理轮次，返回新增数量。
- `pending_batches(db_path: Path, flush: bool=False) -> list[list[dict]]`：调用 Task 3 接口返回待处理批次。
- `commit_update(db_path: Path, batch_ids: list[tuple[str,str]], update: dict, expected_version: int) -> int`：一个课程/会话批次内写入总结和处理标记，返回新课程版本；版本不符则冲突。
- `export_course(db_path: Path, course_id: str, output_dir: Path, timezone: str) -> list[Path]`：生成 current-state.md 与 logs/YYYY-MM-DD.md。
- `update` 字段：`course_id, session_id, events[{source_turn_ids, concept_ids, question, explanation_status, mastery_evidence, links, correction_of}], next_start`；引用轮次必须属于提交批次，升级掌握状态必须附用户表现证据。
- CLI：`import --db PATH --input JSON`、`pending --db PATH [--flush]`、`commit --db PATH --input JSON --expected-version N`、`export --db PATH --course ID --out DIR --timezone ZONE`。CLI 不调用模型，内容总结由当前学习助手完成。

- [ ] 编写失败测试：四轮提交后 pending 为空；重复提交不生成新日志；事务异常后处理标记和课程版本均未推进；两个写入者使用同版本时仅一个成功。
- [ ] 编写失败测试：两轮手动提交后新两轮仍需等待；同日多批均保留；跨午夜按引用消息时间拆分日期；摘要生成时间不替代学习时间；路径中的中文可正确保存。
- [ ] 编写失败测试：导出中断后再次导出与干净导出一致；无效课程 ID 不能越出输出目录；错误的轮次引用、无证据的掌握升级被拒绝。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_store.py' -v` 与 `test_export.py`，确认失败后实现。
- [ ] 以 SQLite 事务保存原始轮次、批次总结、事件、版本和处理检查点；Markdown 为可重建输出。单个文件先写同目录临时文件再替换，导出失败与保存失败分别报告。
- [ ] 实现 CLI 及输出，保留未成功处理批次；新原始轮次可保存，失败总结不能推进已处理位置。
- [ ] 重跑测试；在临时目录通过 CLI 执行 import → pending → commit → export → 重复执行，确认一份状态与不重复日志。提交实现与测试。

### Task 5: 验证实际网页学习回读

**Files:** Update `templates/project-instructions.md`、`docs/integration-capabilities.md`；Create `personal/evidence/roundtrip.md`、真实单课程示范输出。

**Interfaces:** 使用 Task 1 已验证的读取途径和 Task 4 CLI，不新增未证实的网页 API。给网页的学习上下文至少包含课程名、更新时间、当前疑问、相关概念、来源和下次起点。

- [ ] 在 Task 1 选定路径下，将一段真实学习对话转换为合同格式；能验证完整四轮则执行四轮批次，否则展示有明确标识的手动 flush，不伪装成自动触发。
- [ ] 生成基于对话证据的摘要，保存并打开每日记录与当前状态，核对原文和页码。课程概念错误先更正，不能直接沉淀为权威资料。
- [ ] 生成与实际模式匹配的 Project 指令及可导入学习状态。需要用户上传时提供文件和精确操作步骤；工具没有获得发送消息授权时，不向其他对话发送测试问题。
- [ ] 使用可授权执行的实际回读途径验证新网页学习能找到最新状态。若需用户在网页执行一步验证，提供一个具体测试问题并保留该步骤未完成，不能用本地回读代替。
- [ ] 记录触发方式、人工步骤、读取版本及实际结果；没有 turn_end_trigger 的模式明确标“手动同步”或“对话内尽力遵循”，不标“可靠自动保存”。
- [ ] 提交不含个人内容的使用说明与能力报告。真实回读失败时说明受阻能力和可工作的部分，并将自动接入列为独立后续任务。

### Task 6: 准备 GitHub 发布包

**Files:** Create `README.md`、`scripts/build_release.py`、`tests/test_release.py`；Update `.gitignore`。

**Interfaces:** `build_release(repo_dir: Path, out_dir: Path) -> Path`：仅打包 skills/study-companion、templates、README.md 及实际运行所需依赖声明；排除 personal、docs、测试证据、缓存和密钥。发布代码、模板及 Skill，尚未授权公开的课程个人内容不进入包。

- [ ] 编写失败测试：向 personal、docs 和根目录放入合成敏感标记文件，包内不存在；缺失 SKILL.md 或引用资源时打包失败。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_release.py' -v` 确认失败，再实现白名单打包。
- [ ] 写 README：当前确实支持的模式、安装方式、手动更新、数据位置、课程扩展、失败恢复及网页版限制；区分 GitHub 存储和 Skill 安装，不声称推送即自动安装。
- [ ] 完整运行 `python -m unittest discover -s tests -v`、Skill 校验，以及解压发布包后的临时目录 CLI 往返；检查压缩包清单和个人标记缺失。
- [ ] 提交发布准备文件，并展示可审阅的包和验证结果。
- [ ] 内容完成后再确定目标 GitHub 仓库及可见性；用户原请求授权上传，但未指定目标，不能猜测公开设置。确定后使用可用 Git/CLI 能力推送并核实远程内容；如创建 PR，调用 attach_artifact。

## 完成报告与诚实的状态划分

完成报告分开列出：Skill 已验证、资料覆盖范围、记录机制测试、网页回读结果、自动触发能力、GitHub 上传结果。任何一项没有证据则写未完成或受阻，不用整体“完成”掩盖。

## 计划自审

- 设计覆盖：课程资料与权重 → Task 2；场景识别 → Task 2；四轮与手动更新 → Task 3、4；日期与恢复 → Task 4；网页读取保存回读 → Task 1、5；发布与个人数据分离 → Task 6。
- 接口一致：消息唯一键统一为 `(thread_id, turn_id)`；批次隔离统一为课程、会话、对话；成功检查点由事务提交推进。
- 能力限制：未定义虚构网页端点；回读未成功时不能报完成；额外后台基础设施需要单独方案。
- Review Focus 五项均映射到具体测试或实际能力验收。
- 执行建议：由当前助手顺序实施，末尾按执行技能要求进行一次独立审查；用户可选择逐任务子代理实施与审查，代价是更多上下文开销。

状态：用户已确认并选择当前助手顺序实施；新增首次使用专业与学历入口。实施中。
