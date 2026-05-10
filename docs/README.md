# 港口AI智能平台 — Phase 1a

港口领域 AI 对话平台，支持自然语言查询港口生产数据（NL2SQL）、检索港口知识文档（RAG），覆盖船舶/集装箱/泊位/堆场/闸口/设备/能耗 7 大业务域。

## 技术栈

| 层 | 技术 |
|---|------|
| LLM | Ollama + Qwen3-8B（OpenAI 兼容 API） |
| Embedding | Ollama + BGE-M3（1024 维） |
| 向量库 | ChromaDB（嵌入式） |
| 数据库 | SQLite（分域多文件：production/equipment/energy/sessions） |
| 后端 | FastAPI + SSE 流式推送 |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + Zustand |

## 快速启动

### 前置条件

- Python 3.11+
- Node.js 18+
- Ollama（需预下载模型）

```bash
# 安装 Ollama 并下载模型
ollama pull qwen3:8b
ollama pull bge-m3
```

### 开发环境启动

```bash
# 1. 安装依赖
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 2. 初始化演示数据（SQLite + ChromaDB）
python scripts/init_demo_data.py
python scripts/ingest_documents.py

# 3. 启动后端（端口 8000）
cd backend && python -m uvicorn app.main:app --reload --port 8000

# 4. 启动前端（端口 5173，自动代理 /api → 8000）
cd frontend && npm run dev
```

浏览器打开 http://localhost:5173 即可使用。

### Docker 部署

```bash
docker compose up -d
# 访问 http://localhost:80
```

## 项目结构

```
port-ai-platform/
├── backend/
│   ├── app/
│   │   ├── api/              # REST + SSE 端点
│   │   │   ├── chat.py       # POST /chat/stream (SSE)
│   │   │   ├── session.py    # 会话 CRUD
│   │   │   ├── knowledge.py  # 知识库管理
│   │   │   └── health.py     # 健康检查
│   │   ├── conversation/     # 对话管理
│   │   │   ├── intent_router.py    # LLM + YAML 规则意图分类
│   │   │   ├── context_manager.py  # 上下文窗口管理
│   │   │   ├── history_manager.py  # 历史消息持久化
│   │   │   └── session_store.py    # SQLite 会话存储
│   │   ├── nl2sql/           # NL2SQL 引擎
│   │   │   ├── schema_extractor.py  # Schema 提取 + 中文映射
│   │   │   ├── sql_generator.py     # LLM SQL 生成（few-shot + retry）
│   │   │   ├── sql_validator.py     # 5 层安全校验
│   │   │   ├── executor.py          # 只读执行（5s 超时 / 500 行）
│   │   │   ├── result_formatter.py  # 4 档结果格式化
│   │   │   └── pipeline.py          # 完整管线编排
│   │   ├── rag/              # RAG 引擎
│   │   │   ├── document_loader.py  # 多格式文档加载
│   │   │   ├── chunker.py          # Markdown 感知分块
│   │   │   ├── retriever.py        # ChromaDB 检索
│   │   │   ├── generator.py        # LLM 生成（带引用）
│   │   │   └── pipeline.py         # 完整管线编排
│   │   └── core/             # 基础设施
│   │       ├── config.py           # pydantic-settings 配置
│   │       ├── logging.py          # loguru + trace_id
│   │       ├── exceptions.py       # 全局异常处理
│   │       ├── middleware.py        # slowapi 限流
│   │       └── database/           # SQLite 多库客户端
│   └── tests/                # 单元测试（137 用例）
├── frontend/
│   └── src/
│       ├── components/       # React 组件（16 组件）
│       ├── store/            # Zustand 状态管理
│       ├── api/              # SSE 客户端 + 类型定义
│       └── styles/           # Tailwind + 港口主题 CSS
├── config/
│   ├── intent_rules.yaml          # 意图规则（正则兜底）
│   ├── security_filter.yaml       # 安全过滤关键词
│   └── schema_descriptions.yaml   # NL2SQL 中文 Schema 映射
├── scripts/
│   ├── init_demo_data.py          # 3 域种子数据初始化
│   └── ingest_documents.py        # 知识文档入库
├── data/
│   ├── sqlite/              # SQLite 数据库文件
│   ├── chromadb/            # ChromaDB 持久化
│   └── documents/           # 港口知识文档（10 份）
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── nginx.conf
```

## Phase 1a 场景（10 个）

| 场景 | 类型 | 示例问题 |
|------|------|---------|
| PROD-001 船舶动态 | NL2SQL | "今晚有哪些船舶到港？" |
| PROD-002 集装箱位置 | NL2SQL | "BC-101 箱在哪个贝位？" |
| PROD-003 泊位计划 | NL2SQL | "未来 3 天泊位占用情况？" |
| PROD-004 堆场容量 | NL2SQL | "堆场现在还剩多少空位？" |
| PROD-005 装卸进度 | NL2SQL | "1 号泊位的工班进度怎么样？" |
| PROD-015 闸口通行 | NL2SQL | "今天闸口通行了多少车？" |
| SAFE-001 安全规程 | RAG | "港口安全管理规定有哪些要求？" |
| SAFE-002 应急预案 | RAG | "危险品泄漏的应急处理流程是什么？" |
| EQUIP-001 设备状态 | NL2SQL | "1 号岸桥目前状态怎么样？" |
| ENERGY-001 能耗数据 | NL2SQL | "这个月港口总用电量是多少？" |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/stream` | SSE 流式对话 |
| GET | `/api/v1/sessions` | 会话列表 |
| POST | `/api/v1/sessions` | 创建会话 |
| GET | `/api/v1/sessions/{id}` | 会话详情 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |
| GET | `/api/v1/knowledge/status` | 知识库状态 |
| POST | `/api/v1/knowledge/upload` | 文档上传 |
| GET | `/api/v1/health` | 健康检查 |

## SSE 事件流

```
connected → intent → thinking → token* → sources? → done
```

- `intent`: 意图分类结果（intent, confidence, reasoning, rule_triggered）
- `thinking`: 管道元数据（SQL, row_count, execution_ms, cache_hit, chunks_retrieved 等）
- `token`: 流式输出文本片段
- `sources`: RAG 来源引用
- `done`: 完成信号（session_id, message_id, latency_ms）

## 设计决策

详见 `docs/architecture.md`。关键取舍：
- **ChromaDB** 嵌入式向量库（零运维，MVP ~250 chunk）
- **SQLite** 分域多文件（零配置，独立扩展）
- **SSE** 单向流式推送（HTTP 代理友好）
- **无鉴权** Phase 1 演示场景
- **if/elif 意图路由** 4 意图简单分支，不引入 Agent 框架
- **SQL 校验层** 多层防御（禁止写入 + EXPLAIN + 只读模式）

## Phase 1b 规划（未开始）

9 个新增场景：故障诊断、维保计划、碳排放核算、费率查询、合同检索、月度报表等。
详见 Phase 1 执行规划文档。
