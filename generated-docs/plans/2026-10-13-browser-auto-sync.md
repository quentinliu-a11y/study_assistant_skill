> 同步日期：2026-10-17。历史设计／计划存档，保留编写时的状态与检查项；当前实现状态请见本目录 README。

# 浏览器学习自动同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Chrome / Edge 的已确认学习会话中自动采集、每四轮调用 OpenAI 更新课程状态，并将记录保存在本机。

**Architecture:** Manifest V3 扩展通过 Native Messaging 连接 Python host；持久队列和预算账本控制模型任务，现有 SQLite 提交与 Markdown 导出继续作为学习记录权威。采集和学习记忆分离，未知日期、内容修订及不确定分类显式保留。

**Tech Stack:** Python 3.11+、SQLite、OpenAI Responses API、Manifest V3、JavaScript、Node 内置测试、Python unittest。产品运行不依赖 Node；Python 侧优先标准库，现有 tzdata 保留。

**Spec:** `generated-docs/designs/2026-10-13-browser-auto-sync-design.md`。用户于 2026-10-13 回复“继续”确认设计；本计划待审阅。

## Global Constraints

- 默认模型 gpt-5.4-mini；每四轮有效学习问答总结；手动更新和结束处理余量。
- 默认应用内预算：每天 1 美元、每月 10 美元，可调。预算只约束本应用。
- 首次必填专业与学习阶段；每会话确认一次；暂停不发起新调用。
- OPENAI_API_KEY 仅由本机读取；Responses 请求 store=false；不向扩展发送密钥。
- 不发送聊天消息、不自动改写 Project Sources；读取最新状态保留复制／下载入口。
- 无可信来源时间不能伪造原始时间；无稳定 ID 不自动入库；旧 v1 格式兼容。
- 个人资料和证据在 personal/；旧 StudyTrace 目录只读；发布文件使用白名单。
- 保留先前选择：当前助手顺序实施，末尾一次独立审查及修复。外部 API 实测需用户在本机配置密钥；没有密钥先完成可运行代码和模拟测试。

## Review Focus

1. 请求发出后进程崩溃：不能无限重试或重复付费；Task 2、3 测试 unknown 状态和预算预留。
2. 午夜与不同来源时间混合：不能把采集日期标为学习原日期；Task 1 测试混合批次。
3. 多标签页与编辑回答：不能重复计数或覆盖旧证据；Task 2、5 测试并发与修订隔离。
4. 暂停时 API 已返回：保留响应但不发布、不发起下一次请求；Task 4 测试竞争顺序。
5. 未知扩展来源、超长消息和中文安装路径：失败应明确且不执行任意文件；Task 6 测试协议和安装路径。

## 文件边界

- 修改 `study_memory/model.py`、`export.py`、`references/data-contract.md`：版本化时间合同。
- 新增 `skills/study-companion/scripts/study_sync/`：`config.py` 配置；`queue.py` 采集与任务；`budget.py` 预算；`openai_client.py` API 适配；`schemas.py` 输出合同；`worker.py` 调度；`protocol.py` 原生消息；`host.py` 操作分发。该目录含 `__init__.py`。
- 新增 `scripts/install_browser_host.py`、`skills/study-companion/scripts/study_sync_host.py`：安装、入口和卸载。
- 新增 `browser-extension/`：manifest、core、extractor、content、background、native-client、popup HTML/JS/CSS；不直接复制未审查的原型整个目录。
- 新增 `tests/test_sync_*.py`、`tests/browser/*.test.mjs`、合成页面 fixture；文档和 release 白名单随交付更新。

## Task 1：兼容可信原始时间与首次观察时间

**Files:** Modify `skills/study-companion/scripts/study_memory/model.py`, `export.py`, `references/data-contract.md`; Create `tests/test_sync_time.py`。

**Interfaces:** `validate_turn(raw: dict) -> dict` 继续支持 v1；v2 增加 `source_time: str|None`, `first_observed_at: str`, `time_basis: source|observed`。规范化 `occurred_at` 作为排序／归档有效时间，要求与所选依据一致，并保存依据字段。既有 revision_hash v1 不变。

- [ ] 写测试 `test_v1_hash_unchanged`、`test_v2_observed_is_labelled`、`test_source_time_required_for_source_basis`、`test_mixed_midnight_archive`；断言未知来源时日志包含“采集日期，原始时间未知”，原始时间可用时仍按原日归档。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_sync_time.py' -v`，确认 RED。
- [ ] 实现版本分支、时间一致性校验和逐条导出标记；保留原数据库，不批量改写历史。
- [ ] 重跑该测试及原 model/export 测试至 GREEN；提交明确文件。

## Task 2：持久采集队列、任务租约和预算

**Files:** Create `study_sync/{__init__,config,queue,budget}.py`, `tests/test_sync_queue.py`, `tests/test_sync_budget.py`, `templates/sync-config.example.json`（模块路径均在上述 scripts 下）。

**Interfaces:** `enqueue(db: Path, envelope: dict) -> dict` 返回 event_id、accepted、status；`claim_job(db, owner, now) -> dict|None`；`finish_job(db, job_id, response: dict) -> None`；`reserve(db, job_id, amount_usd: Decimal, now) -> bool`；`settle(db, job_id, actual_usd: Decimal|None) -> None`。

事件合同含 protocol_version=1、event_id、course_id、session_id、thread_id、user_message_id、assistant_message_id、文本、来源及首次观察时间。服务端计算规范化哈希核对 event_id；相同事件只确认一次，相同源 ID 内容变化写修订待核对。只有确认会话和完整 profile 可接收。队列单独 SQLite，不提前推进学习数据库检查点。

任务状态：pending、leased、request_sent、response_cached、complete、blocked、unknown。租约过期的 request_sent 进入 unknown，其他未请求任务可恢复。每任务一次预算预留，unknown 不释放；本地时区日／月边界使用配置。用 Decimal 和事务防止并发超额。

- [ ] 写队列测试：两连接领取仅一成功；重复提交不增量；篡改 event_id 拒绝；修订不覆盖；重启恢复与 unknown 不自动重试。
- [ ] 写预算测试：每天 1、每月 10 的边界；并发预留；跨月与午夜；unknown 保留；重复结算不重复扣减。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_sync_queue.py' -v` 和 budget 对应命令确认 RED。
- [ ] 实现事务、配置校验、错误状态和最小查询接口；配置不含密钥。
- [ ] 重跑 GREEN，提交。

## Task 3：受预算约束的 OpenAI 结构化调用

**Files:** Create `study_sync/{openai_client,schemas}.py`, `tests/test_sync_api.py`。

**Interfaces:** `classify(turns, profile, course, transport) -> dict` 输出每个稳定轮次 ID 的 study/nonstudy/uncertain 和理由；`summarize(turns, state, concepts, transport) -> dict` 输出既有 update 合同；`request_json(payload, api_key, transport) -> dict` 只对官方 HTTPS Responses endpoint 请求，不跟随转发 Authorization 的跨域重定向。

transport 可注入，默认使用标准库 HTTP 客户端。请求带 store=false、严格 JSON Schema、显式 max_output_tokens；分类上限 2,000、摘要上限 4,000，文本体 UTF-8 最大 128 KiB。以发送体字节数加保守协议余量作为输入预算上界；无法覆盖未知模型计价时暂停，不能按零费用执行。usage 使用总输入／输出量保守结算，不依赖缓存折扣。

- [ ] 写模拟传输测试：请求模型/schema/store 字段；每条分类必须覆盖输入且无重复 ID；拒绝、截断、无效 JSON、不存在的证据引用不被提交。
- [ ] 写错误测试：401/额度错误停止；429/明确服务错误最多三次指数退避；发送后超时返回 unknown；响应格式最多一次修复；所有尝试进入预算预留。
- [ ] RED 后实现；原始网页内容只作为数据块，关闭工具调用，模型不可指定文件路径或预算。
- [ ] GREEN；保存调用 usage 和脱敏错误，不保存密钥；提交。

## Task 4：分类、四轮与学习数据库的事务衔接

**Files:** Create `study_sync/worker.py`, `tests/test_sync_worker.py`; Modify existing store only when a tested interface gap requires it。

**Interfaces:** `run_once(queue_db, study_db, config, client) -> dict`；`flush_session(queue_db, session_id) -> None`；`set_paused(queue_db, session_id, paused) -> None`。调用 Task 2 队列和 Task 3 API，使用现有 import_turns、pending_batches、commit_update、export_course。

四个候选触发分类；确认 study 累计四个触发总结；uncertain 等待 UI 指定类别，nonstudy 不计。flush 分类并处理余量。已缓存结果先持久化再提交学习库，利用现有幂等键恢复跨库中断。同课程串行处理；版本变化重新读取后重建请求，旧响应不可覆盖新状态。

- [ ] 写测试：8 轮两批；三轮不调用摘要；混入闲聊继续积累；手动余量；不确定项不计；缓存响应后崩溃再起不重调 API；同批重试只记一次。
- [ ] 写暂停竞争测试：响应到达后暂停不发布，恢复复用响应；导出失败不重调摘要；多课程不串批。
- [ ] RED 后实现状态机和 status 查询，包含 pending、classified、saved、error、usage，不把缓存当保存。
- [ ] GREEN 并完整回归原记录测试；提交。

## Task 5：浏览器采集、会话入口和可恢复发送

**Files:** Create `browser-extension/{manifest.json,core.js,extractor.js,content.js,background.js,native-client.js,popup.html,popup.js,popup.css}`, `tests/browser/{core,transport,extractor}.test.mjs`, `tests/browser/fixtures/chat.html`。

**Interfaces:** `extractSnapshot(document, url)` 返回稳定消息与完成证据；`reduceSnapshot(state, snapshot)` 返回草稿／完成事件／修订；`enqueueEvent(event)` 持久化 outbox；`connectHost()` 使用 `com.study_companion.sync`；确认回执后才删除 outbox。popup 向 worker 发送固定操作，不直接访问文件或密钥。

基线消息不当作新学习；新问答需要两次一致快照（间隔至少 2 秒）且无生成中信号并出现已完成操作区。无法确认时提示，不自动补 ID。重复渲染、导航间旧 DOM、分支改变和重生成不能产生新进度。恢复连接先发送服务端已知事件核对，再重发未确认项。

- [ ] Node 测试覆盖基线排除、流式草稿、完成判定、缺 ID、跨聊天 DOM、修订、TeX、重复扫描与两个标签页。
- [ ] 测试 worker 被终止后 outbox 恢复、丢回执重发不丢失、来源 URL 不匹配拒绝；先 RED。
- [ ] 实现最小采集和 popup：专业／阶段／时区、课程与会话确认、待分类及学习计数、开始/暂停/立即更新/结束、错误和费用、uncertain 分类、当前状态复制/下载。
- [ ] `node --test tests/browser/*.test.mjs` GREEN；真实 DOM 调试与合成 fixture 结果分开记录；提交。

## Task 6：原生协议、安装卸载和端到端连接

**Files:** Create `study_sync/{protocol,host}.py`, `skills/study-companion/scripts/study_sync_host.py`, `scripts/install_browser_host.py`, `tests/test_sync_native.py`, `docs/browser-setup.md`。

**Interfaces:** `read_frame(stream) -> dict|None`、`write_frame(stream, value) -> None` 使用原生 32 位长度与 UTF-8；输入上限 512 KiB、输出低于 1 MiB。`dispatch(request, context) -> dict` 仅接受设计列出的操作。安装 CLI：`--browser chrome|edge --extension-id ID --python PATH --data-dir PATH [--uninstall]`。

安装仅创建本工具当前用户注册项；校验扩展 ID，生成精确 allowed_origins。启动器使用固定入口与参数安全引用，不执行客户端 shell 文本。路径与 Python 来源必须显示在安装结果。stdout 专用于帧，诊断发 stderr。使用进程内读循环与单一调度线程，防止等待 API 阻塞状态查询。

- [ ] 写帧截断、非法长度、非法 JSON、未知来源、未知操作、中文/空格路径、响应超限分页、缺密钥和卸载保留用户数据库测试；RED。
- [ ] 实现协议和 dry-run 安装输出；测试临时目录与模拟注册表，不修改其他扩展。
- [ ] GREEN 后在用户当前 Windows 环境安装测试，实际扩展 ID 来自安装后的界面，不编造；需要用户操作时给精确步骤。
- [ ] 用真实原生进程执行 profile/session/enqueue/status 往返；没有密钥仍可验证排队状态；提交。

## Task 7：真实验证、打包与发布

**Files:** Modify `README.md`, `START_HERE.md`, `scripts/build_release.py`, `tests/test_release.py`, `docs/integration-capabilities.md`, Skill instructions；Create `personal/evidence/browser-sync-acceptance.md`（忽略）。

- [ ] 增加扩展和 host 白名单文件、v0.2.0 包；合成敏感文件不得进入 ZIP。更新入门、密钥环境变量、连接诊断、预算配置和日期含义。
- [ ] 运行全部 Python 和 Node 测试、Skill 校验、解压包真实入口往返；测试失败必须修复，不靠省略测试通过。
- [ ] 用户本机配置密钥后，先用合成四轮实测 API，记录模型、usage、估算费用、校验结果；之后用用户确认的真实学习会话验证采集到日志。
- [ ] 对 Chrome/Edge 分别记录实际测试结果；没有浏览器或密钥时明确哪些未验证，继续完成不依赖这些条件的工作。
- [ ] 一次独立最终审查；发现问题补回归测试后修复并复测。公共文件检查后提交并按已授权仓库上传，核对远端 SHA。
- [ ] 交付安装包、入口、通过测试数及真实能力边界；不把自动保存说成自动回读。

## 自审与交接

设计所有部分对应 Task 1–7；API/queue/worker/native/extension 接口一致；五项 Review Focus 均有测试任务。旧库只通过现有写入 API 更新，新队列和预算独立；发布和真实验证分别报告。

沿用当前助手顺序实施方式。用户审阅本计划后进入 executing-plans，先确认适用工作区隔离方式，再执行 Task 1。现在未安装扩展、未启动付费调用、未修改既有个人数据库。
