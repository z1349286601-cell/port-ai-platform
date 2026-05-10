# 港口AI智能平台 — 架构文档

## 系统架构概览

```
┌─────────────┐     SSE (HTTP)      ┌──────────────┐
│   前端 SPA   │ ◄─────────────────► │   FastAPI     │
│  React 18   │   /api/v1/chat/     │   后端服务     │
│  localhost   │      stream        │   port 8000   │
│   :5173      │                     │               │
└─────────────┘                     └───┬───┬───┬───┘
                                        │   │   │
                              ┌─────────┘   │   └─────────┐
                              ▼             ▼             ▼
                         ┌─────────┐  ┌─────────┐  ┌──────────┐
                         │ NL2SQL  │  │   RAG   │  │ Convers. │
                         │ Engine  │  │ Engine  │  │  Manager │
                         └────┬────┘  └────┬────┘  └────┬─────┘
                              │            │            │
                    ┌─────────┴──┐  ┌──────┴──────┐    │
                    ▼            ▼  ▼             ▼    ▼
              ┌──────────┐ ┌──────────┐  ┌──────────────┐
              │ SQLite   │ │ ChromaDB │  │ Ollama        │
              │ 4 域 .db │ │ (BGE-M3) │  │ Qwen3-8B     │
              └──────────┘ └──────────┘  └──────────────┘
```

## 请求处理流程

```
用户消息
    │
    ▼
┌──────────────┐
│ 安全过滤      │  context.sanitize_input() — SQL注入/XSS/jailbreak检测
└──────┬───────┘
       ▼
┌──────────────┐
│ 上下文管理     │  context_manager.build() — 消息历史 + 窗口截断
└──────┬───────┘
       ▼
┌──────────────┐
│ 意图分类      │  intent_router.classify()
│              │  ├─ LLM (Qwen3-8B): 4类 + confidence
│              │  └─ YAML 规则兜底: confidence < 0.7 时
└──────┬───────┘
       ├── document_qa ──→ RAG Pipeline
       ├── data_query  ──→ NL2SQL Pipeline
       ├── mixed       ──→ RAG + NL2SQL
       └── chitchat    ──→ 直接 LLM 回复
```

## NL2SQL 管线

```
用户问题
    │
    ▼
┌─────────────────┐
│ Schema 提取       │  读取 SQLite schema → 中文描述映射
└──────┬──────────┘
       ▼
┌─────────────────┐
│ SQL 生成 (LLM)   │  6 few-shot examples + schema prompt
│ (few-shot cache) │  缓存命中时跳过 LLM 调用
└──────┬──────────┘
       ▼
┌─────────────────┐      Retry ×3 on error
│ SQL 校验          │◄──────────────────────┐
│ 1. SELECT only   │                       │
│ 2. 禁止关键字     │    ┌──────────────────┘
│ 3. 多语句检测     │    │ 错误纠正 (LLM)
│ 4. 括号平衡       │    │ 传入错误信息 + 原SQL
│ 5. EXPLAIN 校验   │    │
└──────┬──────────┘
       ▼
┌─────────────────┐
│ SQL 执行          │  只读模式 / 5s超时 / 500行限制
└──────┬──────────┘
       ▼
┌─────────────────┐
│ 结果格式化        │  0行: 未找到 / 1行: 逐字段 / 2-10: 表格
│                  │  11+: 样本+总数 / 流式输出逐 chunk
└─────────────────┘
```

## RAG 管线

```
用户问题
    │
    ▼
┌─────────────────┐
│ Query Embedding  │  BGE-M3 → 1024维向量
└──────┬──────────┘
       ▼
┌─────────────────┐
│ ChromaDB 检索     │  top_k=5 相似度检索
└──────┬──────────┘
       ▼
┌─────────────────┐
│ LLM 生成         │  System Prompt + 检索chunks + 问题
│ (anti-hallucin.) │  找不到就说"未找到"，禁止编造
└──────┬──────────┘
       ▼
┌─────────────────┐
│ 来源引用          │  [来源: 文档名, 章节] 格式
└─────────────────┘
```

### 文档入库流程

```
PDF/MD/DOCX → DocumentLoader → MarkdownChunker (512 token)
→ BGE-M3 Embedding → ChromaDB (metadata: doc_name, section_title, chunk_index)
```

## 数据库设计

### 分域策略

| 域 | 文件 | 表数 (1a) | 用途 |
|----|------|----------|------|
| production | production.db | 11 | 船舶/集装箱/泊位/堆场/闸口/工班 |
| equipment | equipment.db | 5 | 设备台账/运行/IOT监控 |
| energy | energy.db | 2 | 电力消耗/碳排放 |
| sessions | sessions.db | 2 | 会话/消息持久化 |

### 命名规范

- `dim_*`: 维度表（如 dim_vessel, dim_device）
- `fact_*`: 事实表（如 fact_container, fact_vessel_schedule）
- `agg_*`: 汇总表（如 agg_operation_volume_daily）

## 安全设计

### NL2SQL 安全（5 层）

1. **危险关键字检测**: INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/PRAGMA 拦截
2. **危险函数检测**: sqlite_version/load_extension/readfile/writefile 拦截
3. **多语句检测**: 分号分隔的多语句拦截
4. **只读模式**: SQLite 连接以 `mode=ro` 打开，即使校验层被绕过也无法写入
5. **资源限制**: 5s 超时 + 500 行上限 + 仅允许 SELECT

### 输入安全

- SQL 注入关键词检测
- 路径遍历检测
- Jailbreak prompt 检测（中文+英文）
- 重复字符 DDoS 防护（>500 连续重复截断）
- 文档内容角色注入防护

### 速率限制

- 每 IP 每分钟 30 请求（slowapi）

## 部署架构

```
                    ┌──────────┐
                    │  Nginx   │  :80
                    └──┬───┬───┘
                       │   │
              ┌────────┘   └────────┐
              ▼                     ▼
       ┌──────────┐          ┌──────────┐
       │ Backend  │          │ Frontend │
       │ :8000    │          │ :80      │
       │ FastAPI  │          │ nginx    │
       └────┬─────┘          │ static   │
            │                └──────────┘
       ┌────┴─────┐
       ▼          ▼
  ┌─────────┐ ┌───────┐
  │ Ollama  │ │ Data  │
  │ :11434  │ │ /data │
  └─────────┘ └───────┘
```

- Backend 通过 `host.docker.internal` 访问宿主机的 Ollama
- 数据目录（SQLite/ChromaDB/logs）通过 volume mount 持久化
- Nginx 反向代理，SSE 禁用 buffering

## 关键指标

| 指标 | Phase 1a 目标 |
|------|-------------|
| 信息查询准确率 | ≥ 90% |
| 知识检索准确率 | ≥ 85% |
| 单请求响应时间 | < 5s |
| Docker 启动时间 | < 2min |
| 单元测试覆盖率 | > 80% |
