#!/usr/bin/env python3
"""
RAG 检索工具（通用版）
- 轻量级检索，不含Agentic决策
- 向量检索 + 关键词检索（自动切换）
- 配置从 config.yaml 读取

用法:
  python rag_helper.py --query "你的问题"
  python rag_helper.py --query "你的问题" --strategy vector|keyword|auto
  python rag_helper.py --stats
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
    get_embed_model, get_top_k
)


def load_vectors():
    """加载向量数据库"""
    vectors_file = get_vectors_file()
    if not os.path.exists(vectors_file):
        print(f"[ERROR] 向量数据库不存在: {vectors_file}")
        print("[HINT] 请先运行: python embed_wiki.py")
        return None, []

    with open(vectors_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    chunks = data.get('chunks', [])
    return metadata, chunks


def get_embedding(text):
    """生成查询向量"""
    api_url = get_ollama_api('embeddings')
    model = get_embed_model()
    try:
        resp = requests.post(
            api_url,
            json={"model": model, "prompt": text[:500]},
            timeout=30
        )
        resp.raise_for_status()
        return np.array(resp.json()["embedding"])
    except Exception as e:
        print(f"[WARN] 查询向量生成失败: {e}")
        return None


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)


def vector_search(query, top_k=None):
    """向量检索"""
    top_k = top_k or get_top_k()
    metadata, chunks = load_vectors()
    if not chunks:
        return None, []

    query_embedding = get_embedding(query)
    if query_embedding is None:
        return None, []

    results = []
    for chunk in chunks:
        emb = chunk.get('embedding')
        if emb is not None:
            sim = cosine_similarity(query_embedding, np.array(emb))
            results.append((chunk, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return metadata, results[:top_k]


def keyword_search(query, top_k=None):
    """关键词检索（备用）"""
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
                    "score": score
                })
        except:
            continue

    results.sort(key=lambda x: x['score'], reverse=True)
    return [(r, r['score']/100) for r in results[:top_k]]


def agentic_rag(query, strategy='auto'):
    """
    检索主函数
    strategy: 'vector' | 'keyword' | 'auto'
    """
    results = []
    used_strategy = ""
    model_name = None

    if strategy in ('auto', 'vector'):
        metadata, vector_results = vector_search(query)
        if vector_results:
            model_name = metadata.get('model', 'unknown') if metadata else 'unknown'
            results = [(chunk, score) for chunk, score in vector_results]
            used_strategy = "vector"
            return {
                "query": query,
                "strategy": used_strategy,
                "model": model_name,
                "results": results
            }

    if strategy in ('auto', 'keyword'):
        keyword_results = keyword_search(query)
        if keyword_results:
            results = keyword_results
            used_strategy = "keyword"
            return {
                "query": query,
                "strategy": used_strategy,
                "results": results
            }

    return {"query": query, "strategy": "none", "results": []}


def print_results(response):
    """格式化打印结果"""
    print(f"\n{'='*60}")
    print(f"查询: {response['query']}")
    print(f"策略: {response['strategy']}")
    if 'model' in response and response['model']:
        print(f"模型: {response['model']}")
    print(f"{'='*60}\n")

    if not response['results']:
        print("[RESULT] 未找到相关内容")
        return

    for i, item in enumerate(response['results'], 1):
        if isinstance(item, tuple) and len(item) == 2:
            chunk, score = item
            if isinstance(chunk, dict):
                file_name = chunk.get('file', chunk.get('file_path', ''))
                content = chunk.get('content', '')
            else:
                file_name = str(chunk)
                content = ''
            print(f"[结果 {i}] 相似度: {score:.4f}")
            print(f"文件: {file_name}")
            print(f"内容:")
            print(content[:300])
        print("-" * 60)


def show_stats():
    """显示统计"""
    metadata, chunks = load_vectors()
    if not metadata:
        return
    print("=" * 50)
    print("向量数据库统计")
    print("=" * 50)
    print(f"  模型:       {metadata.get('model', 'unknown')}")
    print(f"  总chunks:   {metadata.get('total_chunks', len(chunks))}")
    print(f"  构建时间:   {metadata.get('build_time', 'unknown')}")
    print(f"  版本:       {metadata.get('version', 'unknown')}")
    if chunks:
        lengths = [len(c.get('content', '')) for c in chunks]
        avg = sum(lengths) / len(lengths)
        short = sum(1 for l in lengths if l < 100)
        print(f"  平均长度:   {avg:.0f} 字符")
        print(f"  <100字符:   {short} ({short/len(chunks)*100:.1f}%)")
    print("=" * 50)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python rag_helper.py --query '查询内容' [--strategy vector|keyword|auto]")
        print("  python rag_helper.py --stats")
        print("  python rag_helper.py --test")
        return

    if sys.argv[1] == "--stats":
        show_stats()
        return

    if sys.argv[1] == "--query":
        if len(sys.argv) < 3:
            print("[ERROR] 请提供查询内容")
            return
        query = sys.argv[2]
        strategy = 'auto'
        if len(sys.argv) > 4 and sys.argv[3] == '--strategy':
            strategy = sys.argv[4]
        response = agentic_rag(query, strategy)
        print_results(response)

    elif sys.argv[1] == "--test":
        test_queries = ["组织简介", "项目介绍", "活动总结"]
        for query in test_queries:
            print(f"\n{'#'*60}")
            response = agentic_rag(query)
            print_results(response)


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
