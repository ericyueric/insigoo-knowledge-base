#!/usr/bin/env python3
"""
Agentic RAG - 智能体化的RAG系统（通用版）
- 自动判断是否需要检索知识库
- 向量检索 + 关键词检索（双策略）
- 基于检索结果生成答案
- 配置从 config.yaml 读取

用法:
  python agentic_rag.py "你的问题"              # 查询（自动判断是否检索）
  python agentic_rag.py "你的问题" --no-decide   # 跳过决策，直接检索
  python agentic_rag.py --build                  # 构建向量数据库
  python agentic_rag.py --test                   # 运行测试用例
"""

import os
import sys
import json
import requests
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    get_wiki_dir, get_vectors_file, get_ollama_api,
    get_embed_model, get_gen_model, get_top_k
)


# =================== Ollama 调用 ===================

def call_ollama_generate(prompt, temperature=0.3, max_retries=3):
    """调用Ollama生成回答"""
    api_url = get_ollama_api('generate')
    model = get_gen_model()
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                api_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": 4096
                    }
                },
                timeout=120
            )
            resp.raise_for_status()
            return resp.json()["response"]
        except Exception as e:
            print(f"[WARN] Ollama调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
    return None


def get_embedding(text, max_retries=3):
    """生成文本嵌入向量"""
    api_url = get_ollama_api('embeddings')
    model = get_embed_model()
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                api_url,
                json={"model": model, "prompt": text[:500]},
                timeout=30
            )
            resp.raise_for_status()
            return np.array(resp.json()["embedding"])
        except Exception as e:
            print(f"[WARN] 嵌入生成失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
    return None


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)


# =================== 向量检索 ===================

def load_vectors():
    """加载向量数据库"""
    vectors_file = get_vectors_file()
    if not os.path.exists(vectors_file):
        print(f"[ERROR] 向量数据库不存在: {vectors_file}")
        print("[HINT] 请先运行: python agentic_rag.py --build")
        return None

    print(f"[LOAD] 加载向量数据库...")
    with open(vectors_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for chunk in data['chunks']:
        chunk['embedding'] = np.array(chunk['embedding'])

    print(f"[OK] 加载成功: {len(data['chunks'])} 个向量")
    return data['chunks']


def vector_search(query, chunks, top_k=None):
    """向量检索"""
    top_k = top_k or get_top_k()
    print(f"[SEARCH] 生成查询向量...")
    query_vector = get_embedding(query)
    if query_vector is None:
        return []

    print(f"[SEARCH] 计算相似度...")
    results = []
    for chunk in chunks:
        if chunk.get('embedding') is None:
            continue
        sim = cosine_similarity(query_vector, chunk['embedding'])
        results.append({
            "file": chunk.get('file', ''),
            "file_path": chunk.get('file_path', ''),
            "content": chunk['content'],
            "similarity": float(sim),
            "chunk_id": chunk.get('chunk_id', 0)
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    print(f"[OK] 找到 {len(results[:top_k])} 个相关结果")
    return results[:top_k]


def keyword_search(query, top_k=None):
    """关键词检索（备用策略）"""
    top_k = top_k or get_top_k()
    wiki_dir = Path(get_wiki_dir())
    results = []
    keywords = query.lower().split()

    for md_file in wiki_dir.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            score = sum(content.lower().count(kw) for kw in keywords)
            if score > 0:
                results.append({
                    "file": md_file.name,
                    "file_path": str(md_file.relative_to(wiki_dir)),
                    "content": content[:500],
                    "similarity": score / 100,
                    "chunk_id": 0
                })
        except:
            continue

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


# =================== Agentic 决策 ===================

def agentic_decide(query, context_usage=30):
    """
    Agentic核心：判断是否需要检索知识库
    返回: {"need_retrieve": bool, "reason": str, "keywords": [str]}
    """
    prompt = f"""你是一个知识库助手的决策模块。你需要判断是否需要检索知识库来回答用户问题。

当前状态：
- 用户问题：{query}
- 上下文使用率：{context_usage}%
- 上下文使用率>60%时，只检索最相关的内容（2-3段）
- 上下文使用率<60%时，可以检索更多内容（3-5段）

判断规则：
1. 如果问题涉及组织内部知识、项目信息、流程制度、历史记录等，需要检索
2. 如果是闲聊、问候、通用常识、简单计算，不需要检索
3. 如果上下文使用率>70%，优先不检索（避免超限）

输出格式（严格JSON）：
{{
  "need_retrieve": true或false,
  "keywords": ["关键词1", "关键词2"],
  "reason": "判断原因"
}}"""

    response = call_ollama_generate(prompt, temperature=0.1)

    if not response:
        # Ollama调用失败，默认检索（保守策略）
        return {"need_retrieve": True, "reason": "决策模块不可用，默认检索", "keywords": [query]}

    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        print(f"[WARN] JSON解析失败: {e}")

    return {"need_retrieve": True, "reason": "解析失败，默认检索", "keywords": [query]}


def agentic_retrieve(query, chunks, context_usage=30):
    """Agentic检索：自动决策 + 动态调整检索数量"""
    decision = agentic_decide(query, context_usage)

    print(f"\n[AGENT] 决策结果：")
    print(f"   - 是否检索：{decision.get('need_retrieve', True)}")
    print(f"   - 原因：{decision.get('reason', '')}")

    if not decision.get('need_retrieve', True):
        return None

    # 根据上下文使用率动态调整检索数量
    if context_usage > 60:
        top_k = 2
    elif context_usage > 40:
        top_k = 3
    else:
        top_k = get_top_k()

    print(f"   - 检索数量：{top_k}")

    keywords = decision.get('keywords', [query])
    search_query = ' '.join(keywords) if isinstance(keywords, list) else query
    print(f"   - 检索关键词：{search_query}")

    # 优先向量检索，失败则用关键词检索
    results = vector_search(search_query, chunks, top_k=top_k)
    if not results:
        print("[FALLBACK] 向量检索无结果，尝试关键词检索...")
        results = keyword_search(search_query, top_k=top_k)

    if not results:
        print("[RESULT] 无相关内容")
        return None

    return {"decision": decision, "retrieved_chunks": results}


# =================== 答案生成 ===================

def generate_answer(query, retrieval_result):
    """基于检索结果生成答案"""
    if not retrieval_result:
        return call_ollama_generate(f"用户问题：{query}\n\n请直接回答（不使用知识库）。")

    context = ""
    for i, chunk in enumerate(retrieval_result['retrieved_chunks'], 1):
        context += f"\n\n【参考资料 {i}】{chunk['file']} (相似度: {chunk['similarity']:.4f})\n"
        context += chunk['content']

    prompt = f"""你是知识库助手。以下是与用户问题相关的知识库片段：

{context}

用户问题：{query}

要求：
1. 优先基于以上参考资料回答
2. 如果参考资料中没有相关信息，说明"知识库中没有相关信息"，然后基于你的知识回答
3. 回答简洁明了
4. 在回答末尾注明信息来源的文件名（如果有）"""

    return call_ollama_generate(prompt)


# =================== 主流程 ===================

def print_results(query, retrieval_result, answer):
    """格式化输出结果"""
    print(f"\n{'='*60}")
    print(f"查询: {query}")
    if retrieval_result:
        print(f"策略: Agentic RAG")
        decision = retrieval_result.get('decision', {})
        print(f"决策: {decision.get('reason', '')}")
    else:
        print(f"策略: 直接回答（未检索知识库）")
    print(f"{'='*60}\n")

    if retrieval_result:
        print("[检索到的参考资料]")
        for i, chunk in enumerate(retrieval_result['retrieved_chunks'], 1):
            print(f"  {i}. {chunk['file']} (相似度: {chunk['similarity']:.4f})")
        print()

    print("[回答]")
    print(answer)
    print(f"\n{'='*60}")


def run_test():
    """运行测试用例"""
    test_queries = [
        "组织简介",
        "项目进展",
        "如何参与志愿活动",
    ]
    chunks = load_vectors()
    if not chunks:
        return

    for query in test_queries:
        print(f"\n{'#'*60}")
        print(f"# 测试: {query}")
        print(f"{'#'*60}")
        retrieval_result = agentic_retrieve(query, chunks)
        answer = generate_answer(query, retrieval_result)
        print_results(query, retrieval_result, answer)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python agentic_rag.py '你的问题'           # 查询")
        print("  python agentic_rag.py '你的问题' --no-decide  # 跳过决策，直接检索")
        print("  python agentic_rag.py --build               # 构建向量数据库")
        print("  python agentic_rag.py --test                # 运行测试用例")
        print("\n示例:")
        print("  python agentic_rag.py '零废弃分类标准是什么'")
        print("  python agentic_rag.py '上次社区活动的总结' 40")
        return

    # 构建命令
    if sys.argv[1] == "--build":
        print("="*60)
        print("构建向量数据库")
        print("="*60 + "\n")
        from embed_wiki import main as embed_main
        embed_main()
        return

    # 测试命令
    if sys.argv[1] == "--test":
        run_test()
        return

    # 正常查询
    query = sys.argv[1]
    context_usage = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30
    skip_decide = '--no-decide' in sys.argv

    print("="*60)
    print("Agentic RAG 系统")
    print("="*60)
    print(f"\n[QUERY] {query}")
    print(f"[CONTEXT] 上下文使用率: {context_usage}%\n")

    chunks = load_vectors()
    if not chunks:
        return

    if skip_decide:
        print("[MODE] 跳过决策，直接检索")
        results = vector_search(query, chunks)
        retrieval_result = {"decision": {"reason": "用户指定直接检索"}, "retrieved_chunks": results}
    else:
        retrieval_result = agentic_retrieve(query, chunks, context_usage)

    answer = generate_answer(query, retrieval_result)
    print_results(query, retrieval_result, answer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n[取消]')
    except Exception as e:
        import traceback
        print(f'CRASH: {e}')
        print(traceback.format_exc())
        sys.exit(1)
