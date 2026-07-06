---
name: insigoo-knowledge-base
version: 1.0.0
description: 组织知识库建设标准与工具集 —— LLM Wiki三层索引 + 可选Agentic RAG向量检索。帮助任何组织（尤其非技术背景的公益机构）建立可维护、可检索、AI友好的知识库。
author: insigoo (因思阁)
license: MIT
tags: [knowledge-base, rag, llm-wiki, index, ollama]
---

# 组织知识库建设标准 (Org Knowledge Base)

> **版本**: v1.0 | **适用对象**: 任何希望建立AI友好知识库的组织
> **特别适合**: 公益机构、社会团体、研究小组（非技术背景可操作）

---

## 这是什么？

一套**经过实战验证的知识库建设标准 + 开箱即用的工具集**，帮助你：

1. **结构化沉淀组织知识** —— 不再散落在微信/邮件/个人电脑里
2. **让AI能读懂你的知识** —— LLM（大语言模型）友好的文档格式
3. **可选：搭建本地AI问答** —— 基于Ollama的私有RAG，数据不出本机

### 三大核心模块

| 模块 | 必选 | 解决什么问题 |
|------|------|-------------|
| **LLM Wiki 标准** | ✅ 必选 | 文档怎么写，AI才读得懂 |
| **三层索引体系** | ✅ 必选 | 知识怎么组织，才找得到 |
| **Agentic RAG** | ⚙️ 可选 | 本地AI问答，数据隐私 |

### 为什么需要"标准"？

**没有标准的知识库 = 垃圾堆**：
- 文件命名混乱 → 找不到
- 格式不统一 → AI读不懂
- 没有索引 → 检索靠运气
- 无法维护 → 三个月就荒废

**有标准的知识库 = 活资产**：
- 命名规范 → 秒级定位
- Markdown格式 → AI直接消费
- 三层索引 → 多维度检索
- 维护流程 → 持续增值

---

## 快速开始（3步）

### 第1步：初始化

```bash
cd insigoo-knowledge-base/scripts
python setup.py
```

配置向导会问你：
1. 知识库根目录放哪？（建议：`./my-wiki/`）
2. 是否配置RAG？（首次建议选"否"，先把Wiki建起来）

生成 `config.yaml` 配置文件。

### 第2步：按标准写文档

阅读 [references/llm_wiki_standard.md](references/llm_wiki_standard.md)，按LLM Wiki标准编写 `.md` 文件，放入 `wiki/` 目录。

参考 [templates/knowledge_index.md](templates/knowledge_index.md) 建立三层索引。

### 第3步：（可选）启用RAG

如果你在第1步选择了配置RAG，或者之后想启用：

```bash
cd insigoo-knowledge-base/scripts
python setup.py --enable-rag
```

参考 [references/rag_setup_guide.md](references/rag_setup_guide.md) 完成Ollama配置。

---

## LLM Wiki 标准（核心）

> **完整标准见**: [references/llm_wiki_standard.md](references/llm_wiki_standard.md)

### 五大原则

| 原则 | 说明 | 反例 |
|------|------|------|
| **纯Markdown** | 只用 `.md`，不用docx/pdf | ❌ 把会议纪要存成 `.docx` |
| **结构化标题** | 用 `#` `##` `###` 组织层级 | ❌ 一大段无标题文字 |
| **元信息前置** | 文件头部声明标题/日期/维护者 | ❌ 不知道谁写的、何时更新 |
| **原子化** | 一个文件一个主题 | ❌ 把所有会议纪要塞一个文件 |
| **可链接** | 用相对路径互相引用 | ❌ 孤立文件，无上下文 |

### 文件头模板

```markdown
# [文档标题]

> **创建**: YYYY-MM-DD | **更新**: YYYY-MM-DD
> **维护者**: [姓名/角色]
> **状态**: 草稿 / 正式 / 归档

---

[正文内容]
```

### 目录结构建议

```
my-wiki/
├── knowledge_index.md      # 三层索引（核心入口）
├── projects/               # 项目知识
│   ├── 项目A/
│   └── 项目B/
├── org/                    # 组织内部
│   ├── meetings/           # 会议纪要
│   ├── policies/           # 制度流程
│   └── members/            # 成员档案
├── methods/                # 方法论/工具
├── cases/                  # 案例库
├── resources/              # 外部资源
└── daily/                  # 日常工作记录
```

---

## 三层索引体系（核心）

> **完整说明见**: [references/three_layer_index.md](references/three_layer_index.md)

### 为什么需要三层索引？

单层索引（只有目录）只能按"位置"找东西。但人脑检索知识是多元的：
- 有时按**位置**找："那个文件在哪个文件夹？"
- 有时按**主题**找："关于零废弃的分类标准，我们有什么资料？"
- 有时按**问题**找："我想知道怎么组织社区活动，去哪查？"

三层索引 = 覆盖三种检索路径。

### 三层结构

| 层级 | 索引维度 | 回答什么问题 | 文件 |
|------|---------|-------------|------|
| **第1层：目录索引** | 按文件位置 | "XX文件在哪？" | knowledge_index.md |
| **第2层：主题索引** | 按知识实体 | "关于XX主题有什么资料？" | knowledge_index.md |
| **第3层：提问场景索引** | 按问题→路径 | "我想知道XX，去哪找？" | knowledge_index.md |

三层索引**写在同一个文件** `knowledge_index.md` 中，用章节分隔。

### 模板

参考 [templates/knowledge_index.md](templates/knowledge_index.md)，包含完整的三层索引模板，可直接复制使用。

---

## 知识库维护标准

> **完整指南见**: [templates/maintenance_guide.md](templates/maintenance_guide.md)

### 维护节奏

| 频率 | 动作 | 耗时 |
|------|------|------|
| **随时** | 新增/修改文档后更新三层索引 | 2分钟 |
| **每周** | 检查是否有孤立文件（未被索引） | 10分钟 |
| **每月** | 审核过时内容，归档或删除 | 30分钟 |
| **每季度** | 重建索引，优化目录结构 | 1小时 |

### 核心原则

1. **写入即索引** —— 新增文档必须同时更新 `knowledge_index.md`
2. **不存废弃** —— 过时文档移入 `archive/`，不直接删
3. **命名带日期** —— `YYYY-MM-DD_主题.md`，方便排序
4. **一人负责** —— 指定知识库管理员，避免"人人有责=无人负责"

---

## Agentic RAG 模块（可选）

> **配置指南见**: [references/rag_setup_guide.md](references/rag_setup_guide.md)

### 什么是Agentic RAG？

**RAG** = Retrieval-Augmented Generation（检索增强生成）
**Agentic** = 智能体化（自动判断是否检索、检索什么）

简单说：让本地AI在回答问题时，**自动参考你的知识库**，而不是凭训练数据瞎编。

### 工作流程

```
用户提问
   ↓
🤖 Agentic决策（是否需要检索知识库？）
   ↓ 是
🔍 向量检索（找最相关的3-5段内容）
   ↓
💡 生成答案（基于检索内容 + 注明来源）
```

### 为什么用Ollama？

| 优势 | 说明 |
|------|------|
| **数据隐私** | 完全本地运行，数据不上传云端 |
| **零成本** | 不消耗API配额 |
| **离线可用** | 无网络也能用 |
| **适合公益机构** | 敏感数据（受益人信息等）不外泄 |

### 何时需要RAG？

| 场景 | 是否需要RAG |
|------|------------|
| 知识库文档<20篇 | ❌ 不需要，LLM Wiki够用 |
| 知识库文档50-200篇 | 🟡 建议，提升检索效率 |
| 知识库文档>200篇 | ✅ 必须，否则找不到东西 |
| 需要AI问答机器人 | ✅ 必须 |
| 涉及敏感数据 | ✅ 建议，本地保护隐私 |

### 技术栈

| 组件 | 推荐 | 说明 |
|------|------|------|
| 嵌入模型 | `nomic-embed-text` | Ollama自带，274MB |
| 生成模型 | `qwen2.5:7b` 或同类 | 本地运行，4-5GB |
| 向量存储 | JSON文件 | 轻量，无需数据库 |
| 检索算法 | 余弦相似度 | 简单可靠 |

---

## 文件结构说明

```
insigoo-knowledge-base/
├── SKILL.md                          # 本文件（主入口）
├── README.md                         # 快速说明
├── scripts/
│   ├── setup.py                      # 配置向导
│   ├── config.yaml                   # 配置文件（setup.py生成）
│   ├── embed_wiki.py                 # 向量化脚本（全量）
│   ├── incremental_update.py         # 增量更新脚本
│   ├── agentic_rag.py                # Agentic RAG查询
│   └── rag_helper.py                 # 简单检索工具
├── templates/
│   ├── knowledge_index.md            # 三层索引模板
│   ├── wiki_structure.md             # 目录结构模板
│   ├── maintenance_guide.md          # 维护指南模板
│   └── config.yaml.example           # 配置文件示例
└── references/
    ├── llm_wiki_standard.md          # LLM Wiki编写标准
    ├── three_layer_index.md          # 三层索引详解
    └── rag_setup_guide.md            # RAG配置指南
```

---

## 使用流程图

```
首次使用
  │
  ├─→ 运行 setup.py（配置向导）
  │     ├─ 选择知识库目录
  │     └─ 是否启用RAG？（否→跳过Ollama配置）
  │
  ├─→ 按 llm_wiki_standard.md 写文档
  │
  ├─→ 用 knowledge_index.md 模板建三层索引
  │
  └─→ 日常维护（maintenance_guide.md）

后续使用
  │
  ├─→ 新增文档 → 更新索引 → （如启用RAG）运行 incremental_update.py
  │
  └─→ 查询知识 → 查索引 / （如启用RAG）运行 agentic_rag.py
```

---

## FAQ

### Q1：我们组织很小，文档不多，需要这个吗？

**A**：文档<20篇不需要RAG，但**LLM Wiki标准 + 三层索引**仍然建议用。好的习惯从第一天开始养成，等文档多了再规范就很痛苦。

### Q2：不懂技术能用吗？

**A**：LLM Wiki标准 + 三层索引部分**完全不需要技术**，会写Markdown即可。RAG模块需要会运行Python命令，建议找技术志愿者帮忙配置一次，后续使用很简单。

### Q3：必须用Ollama吗？能用其他工具吗？

**A**：不必须。RAG模块设计为可替换：
- 嵌入模型：可换OpenAI/智谱等API
- 生成模型：可换任意LLM
- 向量存储：可换Chroma/Milvus等

但Ollama是**零成本、保隐私**的最佳选择，特别适合公益机构。

### Q4：和Notion/飞书文档有什么区别？

**A**：
- Notion/飞书：**平台依赖**，数据在云端，格式封闭
- 本方案：**数据自主**，纯Markdown文件，任何工具都能读

建议：用本方案管理**核心知识资产**，用Notion/飞书做**协作编辑**。

### Q5：知识库多久能建起来？

**A**：
- **第1天**：跑通setup，建好目录结构和索引模板
- **第1周**：把现有重要文档（10-20篇）按标准整理入库
- **第1月**：形成习惯，新文档随手入库随手索引
- **第3月**：知识库开始产生价值，团队依赖它找东西

---

## 设计理念

### 为什么是"标准"而不是"工具"？

工具会过时，标准能传承。这套skill的核心价值不是Python脚本，而是**LLM Wiki的编写标准**和**三层索引的组织方法**。脚本只是辅助，即使不用脚本，按标准写Markdown、按三层索引组织，知识库就能运转。

### 为什么强调"AI友好"？

未来的知识检索会越来越依赖AI。如果你的知识库格式AI读不懂，就无法享受AI带来的效率提升。LLM Wiki标准确保你的知识**现在能用、未来AI也能用**。

### 为什么RAG是可选的？

不同组织需求不同：
- 小组织：LLM Wiki + 索引足够
- 中型组织：加RAG提升检索
- 大型组织：需要更专业的向量数据库

强制RAG会增加门槛（需要Ollama、Python环境），违背"非技术背景可操作"的原则。所以设计为可选模块。

---

## 致谢

本标准源自一线实践，经过多轮迭代验证。感谢所有提供反馈的组织和伙伴。

---

## License

MIT License - 自由使用、修改、分发

---

*版本 v1.0 | 持续迭代中*
