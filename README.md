# 组织知识库建设标准 (Org Knowledge Base)

> **版本**: v1.0 | **License**: MIT
> 帮助任何组织建立AI友好的知识库 —— LLM Wiki标准 + 三层索引 + 可选Agentic RAG

---

## 这是什么？

一套**经过实战验证的知识库建设标准 + 开箱即用的工具集**：

1. **LLM Wiki 标准** —— 文档怎么写，AI才读得懂
2. **三层索引体系** —— 知识怎么组织，才找得到
3. **Agentic RAG**（可选）—— 基于Ollama的本地AI问答，数据不出本机

特别适合**公益机构、社会团体、研究小组**（非技术背景可操作）。

---

## 快速开始

### 方式一：完整配置（推荐）

```bash
cd insigoo-knowledge-base/scripts
python setup.py
```

配置向导会引导你完成：
1. 设置知识库目录
2. 创建目录结构
3. （可选）配置RAG模块

### 方式二：手动配置

1. 复制 `templates/config.yaml.example` 为 `scripts/config.yaml`
2. 编辑配置文件，设置知识库目录
3. 参考 `templates/` 下的模板建立知识库

---

## 文件结构

```
insigoo-knowledge-base/
├── SKILL.md                          # 主入口（完整标准说明）
├── README.md                         # 本文件
├── scripts/
│   ├── setup.py                      # 配置向导
│   ├── config.py                     # 配置加载器
│   ├── embed_wiki.py                 # 向量化脚本
│   ├── incremental_update.py         # 增量更新
│   ├── agentic_rag.py                # Agentic RAG查询
│   └── rag_helper.py                 # 简单检索
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

## 核心文档

| 想了解什么 | 看哪个文件 |
|-----------|-----------|
| 整体介绍和使用流程 | [SKILL.md](SKILL.md) |
| 文档怎么写才标准 | [references/llm_wiki_standard.md](references/llm_wiki_standard.md) |
| 三层索引怎么建 | [references/three_layer_index.md](references/three_layer_index.md) |
| RAG怎么配置 | [references/rag_setup_guide.md](references/rag_setup_guide.md) |
| 日常怎么维护 | [templates/maintenance_guide.md](templates/maintenance_guide.md) |

---

## 三步上手

### 第1步：按标准写文档

阅读 [LLM Wiki编写标准](references/llm_wiki_standard.md)，用Markdown编写文档。

核心要点：
- 纯 `.md` 格式
- 文件头部有元信息
- 结构化标题（`#` `##` `###`）
- 一个文件一个主题

### 第2步：建立三层索引

参考 [三层索引模板](templates/knowledge_index.md)，建立 `knowledge_index.md`。

三层索引：
- 第1层：目录索引（按文件位置）
- 第2层：主题索引（按知识实体）
- 第3层：提问场景索引（按问题→路径）

### 第3步：（可选）启用RAG

如果需要AI问答功能，参考 [RAG配置指南](references/rag_setup_guide.md) 配置Ollama。

```bash
# 配置RAG
python scripts/setup.py --enable-rag

# 构建向量数据库
python scripts/embed_wiki.py

# 查询
python scripts/agentic_rag.py "你的问题"
```

---

## 日常使用

### 新增文档

1. 在 `wiki/` 对应目录创建 `.md` 文件
2. 更新 `knowledge_index.md` 索引
3. （如启用RAG）运行 `python scripts/incremental_update.py`

### 查询知识

- **手动查索引**：打开 `knowledge_index.md`，按三层索引查找
- **AI查询**（如启用RAG）：`python scripts/agentic_rag.py "你的问题"`

### 定期维护

| 频率 | 动作 |
|------|------|
| 随时 | 新增文档后更新索引 |
| 每周 | 检查孤立文件 |
| 每月 | 审核过时内容 |
| 每季度 | 优化目录结构 |

详见 [维护指南](templates/maintenance_guide.md)。

---

## 系统要求

### 基础功能（LLM Wiki + 三层索引）

- 任何能编辑文本的设备
- 会基本Markdown语法

### RAG模块（可选）

- Python 3.8+
- Ollama（本地AI运行环境）
- 内存≥8GB（推荐16GB+）
- 磁盘空间≥6GB（模型+向量数据库）

---

## 常见问题

**Q: 不懂技术能用吗？**
A: LLM Wiki标准 + 三层索引完全不需要技术，会写Markdown即可。RAG模块建议找技术志愿者帮忙配置。

**Q: 必须用Ollama吗？**
A: 不必须。RAG是可选模块。即使不用RAG，按标准写Markdown、按三层索引组织，知识库就能运转。

**Q: 和Notion/飞书文档有什么区别？**
A: 本方案数据自主（纯Markdown文件），不绑定平台。建议用本方案管理核心知识资产，用Notion/飞书做协作编辑。

**Q: 知识库多久能建起来？**
A: 第1天跑通配置，第1周整理10-20篇核心文档，第1月形成习惯，第3月开始产生价值。

---

## License

MIT License - 自由使用、修改、分发

---

*版本 v1.0 | 持续迭代中*
