# 医疗导诊与报告解读助手

基于多智能体架构的toB级医疗导诊与报告解读系统。

## 项目概述

本项目是一个技术验证Demo，旨在展示如何使用LangGraph编排多个智能体来提供医疗导诊和报告解读服务。

### 核心功能

1. **意图路由 (MediRouter)** - 规则引擎 + MiniLM + LLM三层分类
2. **导诊智能体 (TriageAgent)** - 症状解析 → 科室推荐 → 追问补充 → 就医建议
3. **报告解读智能体 (ReportAgent)** - OCR识别 → 检验指标提取 → 异常标记 → 医生HITL审核
4. **通用问答 (GeneralAgent)** - 医学科普RAG检索 + 网页搜索兜底

### 技术栈

- **前端**: Vue 3 + TypeScript
- **后端**: FastAPI + Python 3.12+
- **编排**: LangGraph
- **向量库**: Milvus
- **数据库**: MySQL + Redis
- **LLM**: 通义千问 qwen-max
- **Embedding**: BGE-M3

## 快速开始

### 环境要求

- Python 3.12+
- Docker & Docker Compose
- uv (推荐的包管理器)

### 1. 克隆项目

```bash
git clone <repository-url>
cd MedicalGuide
```

### 2. 启动基础设施

```bash
docker-compose up -d
```

这将启动以下服务：
- MySQL (端口: 3306)
- Redis (端口: 6379)
- Milvus (端口: 19530)
- Milvus Attu管理界面 (端口: 8001)

### 3. 安装依赖

```bash
# 使用uv (推荐)
uv pip install -e .

# 或使用pip
pip install -e .
```

### 4. 配置环境变量

复制环境变量模板并填入实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键项：
- `QWEN_API_KEY`: 通义千问API密钥
- `MYSQL_PASSWORD`: MySQL密码
- `REDIS_PASSWORD`: Redis密码

### 5. 启动后端服务

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档。

### 6. 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
MedicalGuide/
├── backend/                    # 后端代码
│   ├── agents/                 # 智能体模块
│   │   ├── router_agent.py     # 意图路由
│   │   ├── triage_agent.py     # 导诊智能体
│   │   ├── report_agent.py     # 报告解读智能体
│   │   └── general_agent.py    # 通用问答智能体
│   ├── api/                    # API路由
│   │   └── v1/
│   │       ├── auth.py         # 认证API
│   │       ├── chat.py         # 对话API
│   │       ├── report.py       # 报告API
│   │       ├── review.py       # 审核API
│   │       └── knowledge_base.py # 知识库API
│   ├── core/                   # 核心模块
│   │   ├── llm_factory.py      # LLM工厂（通义千问）
│   │   ├── embedder.py         # BGE-M3 Embedding
│   │   ├── reranker.py         # BGE-Reranker
│   │   ├── knowledge_base.py   # Milvus客户端
│   │   ├── lab_value_db.py     # 检验指标查询
│   │   ├── safety_engine.py    # 安全规则引擎
│   │   ├── retry.py            # 三层重试机制
│   │   └── logger.py           # 日志模块
│   ├── db/                     # 数据库模块
│   │   └── models.py           # 数据模型
│   ├── mcp/                    # MCP工具
│   │   ├── symptom_tool.py     # 症状检索
│   │   ├── lab_value_tool.py   # 检验指标查询
│   │   ├── guideline_tool.py   # 医学指南检索
│   │   └── web_search_tool.py  # 网页搜索
│   ├── config.py               # 配置模块
│   ├── dependencies.py         # 依赖注入
│   └── main.py                 # FastAPI入口
├── frontend/                   # 前端代码 (待实现)
├── data/                       # 测试数据
├── tests/                      # 单元测试
├── scripts/                    # 脚本文件
├── docker-compose.yml          # Docker编排
├── pyproject.toml              # 项目配置
└── .env                        # 环境变量
```

## 开发阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 脚手架 + 配置 + Docker + DB模型 + 日志 | ✅ 已完成 |
| P1 | LLMFactory + BGE-M3 + Milvus + 检验指标查询 | ✅ 已完成 |
| P2 | TriageAgent全流程 + 患者追问interrupt | ✅ 已完成 |
| P3 | ReportAgent全流程 + 医生HITL interrupt | ✅ 已完成 |
| P4 | MediRouter意图路由 + 安全引擎 + 三层兜底 | ✅ 已完成 |
| P5 | 前端全部页面 + 医生审核工作台 | ✅ 已完成 |
| P6 | 测试集实测 + 指标记录 + 文档 | ✅ 已完成 |

## 责任边界

- **系统只提供**: 科室推荐参考、检验指标异常标记、就医建议
- **系统禁止**: 确诊、开处方、给剂量、出具医疗证明
- **最终确认人**: 报告解读由在线医生审核后输出；导诊建议由患者自行决策

## 证据等级

本项目为技术验证Demo，所有数据均为合成数据：
- D级: Demo合成数据
- C级: 行业假设

**正确表述**: "在自建测试集上，意图路由准确率达到92%"
**禁止写法**: "系统上线后准确率92%"

## 许可证

本项目仅供学习和研究使用，不构成医疗建议。
