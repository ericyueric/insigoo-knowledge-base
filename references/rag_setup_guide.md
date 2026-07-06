# RAG 配置指南（可选模块）

> **适用对象**: 有一定技术基础的用户（或技术志愿者）
> **目标**: 配置本地AI问答系统，数据隐私不外泄

---

## 什么是RAG？

**RAG = Retrieval-Augmented Generation（检索增强生成）**

简单说：让AI在回答问题时，**参考你的知识库**，而不是凭训练数据瞎编。

```
用户提问
   ↓
🔍 检索知识库（找最相关的内容）
   ↓
💡 AI生成答案（基于检索内容）
   ↓
📝 返回答案 + 注明来源
```

### 为什么用本地Ollama？

| 优势 | 说明 |
|------|------|
| **数据隐私** | 完全本地运行，数据不上传云端 |
| **零成本** | 不消耗API配额 |
| **离线可用** | 无网络也能用 |
| **适合公益机构** | 敏感数据（受益人信息等）不外泄 |

---

## 前置要求

### 硬件要求

| 资源 | 最低 | 推荐 |
|------|------|------|
| 内存 | 8GB | 16GB+ |
| 磁盘空间 | 6GB | 10GB+ |
| CPU | 4核 | 8核+ |
| GPU | 不必须 | 有GPU更快（非必须） |

### 软件要求

| 软件 | 说明 |
|------|------|
| Python 3.8+ | 运行脚本 |
| Ollama | 本地AI运行环境 |
| pip | 安装Python依赖 |

---

## 安装步骤

### 第1步：安装Ollama

#### Windows
1. 访问 https://ollama.com/download
2. 下载 Windows 版本
3. 运行安装程序
4. 验证：打开命令行，运行 `ollama --version`

#### macOS
1. 访问 https://ollama.com/download
2. 下载 macOS 版本
3. 安装后运行 `ollama serve`
4. 验证：`ollama --version`

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

### 第2步：下载AI模型

需要两个模型：

| 模型 | 用途 | 大小 | 下载命令 |
|------|------|------|---------|
| nomic-embed-text | 嵌入模型（向量化文档） | 274MB | `ollama pull nomic-embed-text` |
| qwen2.5:7b | 生成模型（回答问题） | 4.7GB | `ollama pull qwen2.5:7b` |

**轻量替代方案**（内存<16GB）：

| 模型 | 大小 | 质量 |
|------|------|------|
| qwen2:1.5b | 934MB | 较低（但够用） |
| qwen2.5:3b | 2GB | 中等 |

**下载命令**：
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

### 第3步：验证Ollama

```bash
# 检查Ollama运行
ollama list

# 检查API可用
curl http://localhost:11434/api/tags
```

### 第4步：配置config.yaml

运行配置向导：

```bash
cd scripts
python setup.py --enable-rag
```

或手动编辑 `config.yaml`：

```yaml
rag:
  enabled: true
  vectors_dir: ./rag-data
  vectors_file: wiki_vectors.json
  ollama_api: http://localhost:11434
  embed_model: nomic-embed-text
  gen_model: qwen2.5:7b
  top_k: 5
```

### 第5步：构建向量数据库

首次使用，需要把知识库文档向量化：

```bash
cd scripts
python embed_wiki.py
```

**预期输出**：
```
============================================================
LLM Wiki 向量化 v3.0
============================================================
发现 50 个 .md 文件

[1/50] README.md
  -> 5 chunks
...
============================================================
DONE!
  总chunks:    350
  平均长度:    250 字符
  <100字符:    30 (8.5%)
============================================================
```

**耗时**：取决于文档数量和电脑性能
- 20篇文档：约2-5分钟
- 100篇文档：约10-20分钟

### 第6步：测试查询

```bash
cd scripts
python agentic_rag.py "你的组织是做什么的"
```

**预期输出**：
```
============================================================
Agentic RAG 系统
============================================================

[QUERY] 你的组织是做什么的
[CONTEXT] 上下文使用率: 30%

[LOAD] 加载向量数据库...
[OK] 加载成功: 350 个向量

[AGENT] 决策结果：
   - 是否检索：True
   - 原因：涉及组织信息

[SEARCH] 生成查询向量...
[SEARCH] 计算相似度...
[OK] 找到 5 个相关结果

============================================================
查询: 你的组织是做什么的
策略: Agentic RAG
============================================================

[回答]
根据知识库，本组织是一家专注于零废弃倡导的公益机构...
来源：org/intro.md
============================================================
```

---

## 日常使用

### 查询知识库

```bash
# Agentic RAG（推荐，自动判断是否检索）
python agentic_rag.py "你的问题"

# 简单检索（不做决策，直接搜索）
python rag_helper.py --query "你的问题"

# 指定检索策略
python rag_helper.py --query "你的问题" --strategy vector
python rag_helper.py --query "你的问题" --strategy keyword
```

### 更新知识库后

新增/修改文档后，运行增量更新：

```bash
cd scripts
python incremental_update.py
```

### 查看统计

```bash
python embed_wiki.py --stats
# 或
python rag_helper.py --stats
```

---

## 模型选择指南

### 嵌入模型（用于向量化）

| 模型 | 大小 | 语言支持 | 推荐度 |
|------|------|---------|--------|
| nomic-embed-text | 274MB | 中英文 | ⭐⭐⭐⭐⭐ |
| bge-m3 | 1.2GB | 中英文 | ⭐⭐⭐⭐ |

**推荐**：`nomic-embed-text`（轻量、效果好）

### 生成模型（用于回答）

| 模型 | 大小 | 质量 | 内存需求 | 推荐度 |
|------|------|------|---------|--------|
| qwen2.5:7b | 4.7GB | 高 | 8GB+ | ⭐⭐⭐⭐⭐ |
| qwen2.5:3b | 2GB | 中 | 4GB+ | ⭐⭐⭐⭐ |
| qwen2:1.5b | 934MB | 低 | 2GB+ | ⭐⭐⭐ |
| llama3.1:8b | 4.7GB | 高 | 8GB+ | ⭐⭐⭐⭐ |

**推荐**：
- 内存≥16GB：`qwen2.5:7b`
- 内存8-16GB：`qwen2.5:3b`
- 内存<8GB：`qwen2:1.5b`

---

## 高级配置

### 修改chunk切割参数

在 `config.yaml` 中：

```yaml
rag:
  chunk_min_len: 150    # chunk最小长度（字符）
  chunk_max_len: 400    # chunk最大长度
  chunk_table_max: 600  # 表格chunk最大长度
```

**调优建议**：
- 答案太碎片化 → 增大 `chunk_max_len`（如500）
- 答案包含太多无关内容 → 减小 `chunk_max_len`（如300）

### 修改检索数量

```yaml
rag:
  top_k: 5  # 检索返回的相关段落数量
```

**调优建议**：
- 答案不全 → 增大 `top_k`（如8）
- 答案有噪音 → 减小 `top_k`（如3）

### 使用其他Ollama端口

如果默认端口11434被占用：

```bash
# 启动Ollama到其他端口
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

在 `config.yaml` 中：
```yaml
rag:
  ollama_api: http://localhost:11435
```

---

## 故障排查

### Ollama启动失败

```bash
# 检查端口占用
netstat -an | findstr 11434    # Windows
lsof -i :11434                  # macOS/Linux

# 杀掉占用进程后重启
ollama serve
```

### 模型下载失败

```bash
# 检查网络
ollama pull nomic-embed-text

# 如果网络慢，可以设置代理
# 或从镜像源下载
```

### 向量化很慢

**原因**：每个chunk都要调用Ollama生成嵌入

**优化**：
1. 确保Ollama在本地运行（不是远程）
2. 关闭其他占内存的程序
3. 如果有GPU，确保Ollama使用GPU

### 查询结果不相关

**排查**：
1. 检查向量数据库是否最新：`python incremental_update.py`
2. 检查chunk质量：`python embed_wiki.py --stats`
3. 尝试换关键词或换问法
4. 调整 `top_k` 参数

---

## 何时不需要RAG？

| 场景 | 是否需要RAG |
|------|------------|
| 文档<20篇 | ❌ 不需要，三层索引够用 |
| 没有AI问答需求 | ❌ 不需要 |
| 硬件不足（内存<8GB） | ❌ 不建议 |
| 涉及高度敏感数据 | ✅ 建议（本地保护隐私） |
| 文档>50篇 | ✅ 建议 |
| 需要AI客服/问答 | ✅ 必须 |

---

## 安全与隐私

### 数据流向

| 组件 | 数据是否外传 |
|------|------------|
| 知识库文档（.md） | ❌ 完全本地 |
| 向量数据库 | ❌ 完全本地 |
| Ollama嵌入/生成 | ❌ 完全本地 |
| 查询和回答 | ❌ 完全本地 |

**结论**：使用本方案，数据完全不离开你的电脑。

### 注意事项

- ✅ 知识库中可以存储敏感信息（受益人数据等）
- ✅ AI问答过程不外传任何数据
- ⚠️ 如果后续切换到云端API（如OpenAI），数据会上传
- ⚠️ 定期备份向量数据库（`rag-data/` 目录）

---

*RAG是可选模块，根据组织需求决定是否启用*
