#!/usr/bin/env python3
"""
LLM Wiki 向量化脚本 v3.0（通用版）
- Markdown语义切割（标题/段落/代码块/表格感知）
- 每个chunk附完整元数据
- 基于Ollama嵌入模型
- 配置从 config.yaml 读取（无硬编码路径）

用法:
  python embed_wiki.py            # 全量向量化
  python embed_wiki.py --stats    # 查看向量数据库统计
"""

import os
import re
import sys
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# 加载配置
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    get_wiki_dir, get_vectors_file, get_ollama_api,
    get_embed_model, get_chunk_params
)

# =================== 语义切割核心 ===================

def split_markdown_semantic(content, min_len=None, max_len=None, table_max=None):
    """
    按Markdown语义结构切割内容
    策略：
    1. 以标题行（# ## ### ####）为chunk强制边界
    2. 代码块（```）保持完整不切割
    3. 表格保持完整（超长表格才切割）
    4. 普通段落：在句子边界切割，目标长度150-400字符
    """
    params = get_chunk_params()
    min_len = min_len or params['min_len']
    max_len = max_len or params['max_len']
    table_max = table_max or params['table_max']

    lines = content.split('\n')
    chunks = []
    current_lines = []
    current_len = 0
    in_code_block = False
    in_table = False

    def flush_chunk():
        nonlocal current_lines, current_len
        if current_lines:
            chunk_text = '\n'.join(current_lines).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current_lines = []
            current_len = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # --- 代码块 ---
        if stripped.startswith('```'):
            if not in_code_block:
                flush_chunk()
                in_code_block = True
                current_lines = [line]
                current_len = len(line)
            else:
                current_lines.append(line)
                code_text = '\n'.join(current_lines)
                if len(code_text) <= max_len * 2:
                    chunks.append(code_text)
                else:
                    chunks.extend(current_lines)
                current_lines = []
                current_len = 0
                in_code_block = False
            i += 1
            continue

        if in_code_block:
            current_lines.append(line)
            current_len += len(line)
            i += 1
            continue

        # --- 表格 ---
        if stripped.startswith('|') and '|' in stripped[1:]:
            if not in_table:
                flush_chunk()
                in_table = True
            current_lines.append(line)
            current_len += len(line)
            i += 1
            continue
        else:
            if in_table:
                table_text = '\n'.join(current_lines)
                if len(table_text) <= table_max:
                    chunks.append(table_text)
                else:
                    chunks.extend(current_lines)
                current_lines = []
                current_len = 0
                in_table = False

        # --- 标题 ---
        heading_match = re.match(r'^(#{1,4})\s+(.+)', stripped)
        if heading_match:
            flush_chunk()
            current_lines = [line]
            current_len = len(line)
            i += 1
            continue

        # --- 普通行 ---
        current_lines.append(line)
        current_len += len(line)

        if current_len > max_len:
            text = '\n'.join(current_lines)
            cut = find_sentence_boundary(text, min_len)
            if 0 < cut < len(text):
                chunks.append(text[:cut].strip())
                remaining = text[cut:].strip()
                if remaining:
                    current_lines = remaining.split('\n')
                    current_len = len(remaining)
                else:
                    current_lines = []
                    current_len = 0
            else:
                flush_chunk()

        i += 1

    if in_table:
        chunks.append('\n'.join(current_lines))
    else:
        flush_chunk()

    return chunks


def find_sentence_boundary(text, min_from_end=50):
    """从文本末尾往前找句子边界（。！？\n）"""
    for i in range(len(text) - 1, max(0, len(text) - min_from_end - 200), -1):
        if text[i] in '。！？\n' and i > min_from_end:
            return i + 1
    return min(len(text), max(min_from_end, len(text) // 2))


def merge_short_chunks(chunks, min_len=None):
    """合并过短的chunk（<min_len）与下一个chunk"""
    params = get_chunk_params()
    min_len = min_len or params['min_len']
    max_len = params['max_len']

    if not chunks:
        return chunks

    merged = []
    buf = chunks[0]
    for i in range(1, len(chunks)):
        if len(buf) < min_len and len(buf) + len(chunks[i]) <= max_len * 1.5:
            buf = buf + '\n' + chunks[i]
        else:
            merged.append(buf)
            buf = chunks[i]
    merged.append(buf)
    return merged


# =================== 元数据提取 ===================

def extract_title(content):
    """提取文档主标题"""
    for line in content.split('\n'):
        m = re.match(r'^#\s+(.+)', line.strip())
        if m:
            return m.group(1).strip()
    return '无标题'


def extract_hierarchy(content):
    """提取文档层级结构（标题列表）"""
    lines = content.split('\n')
    hierarchy = []
    for line in lines:
        m = re.match(r'^(#{1,4})\s+(.+)', line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            hierarchy.append('  ' * (level - 1) + title)
    return hierarchy


def simple_keywords(text, top_n=5):
    """简单关键词提取（基于词频，支持中英文）"""
    clean = re.sub(r'[#*`>\[\]\(\)\-_\\|]', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    # 中文2-4字短语
    words = []
    for match in re.finditer(r'[\u4e00-\u9fff]{2,4}', clean):
        w = match.group(0)
        if w not in ['这个', '那个', '可以', '已经', '没有', '不是', '我们', '他们']:
            words.append(w)
    # 英文单词
    for match in re.finditer(r'[a-zA-Z]{3,}', clean):
        words.append(match.group(0).lower())
    from collections import Counter
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]


# =================== 向量化 ===================

def get_embedding(text, retry=2):
    """调用Ollama生成嵌入向量"""
    api_url = get_ollama_api('embeddings')
    model = get_embed_model()
    for attempt in range(retry + 1):
        try:
            resp = requests.post(
                api_url,
                json={'model': model, 'prompt': text[:2000]},
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()['embedding']
        except Exception as e:
            if attempt < retry:
                import time
                time.sleep(1)
            else:
                print(f'  [WARN] 嵌入失败: {e}')
                return None


def compute_file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


# =================== 主流程 ===================

def process_file(filepath, wiki_dir):
    """处理单个文件，返回chunks列表（含元数据）"""
    rel_path = str(Path(filepath).relative_to(wiki_dir))

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'  [WARN] 读取失败: {e}')
        return []

    if not content.strip():
        return []

    raw_chunks = split_markdown_semantic(content)
    raw_chunks = merge_short_chunks(raw_chunks)

    print(f'  -> {len(raw_chunks)} chunks')

    doc_title = extract_title(content)
    hierarchy = extract_hierarchy(content)
    file_mtime = os.path.getmtime(filepath)
    file_mtime_iso = datetime.fromtimestamp(file_mtime).isoformat()

    result_chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        embedding = get_embedding(chunk_text)
        if embedding is None:
            continue

        first_line = chunk_text.split('\n')[0][:80]
        section = first_line if first_line else f'chunk_{idx}'

        chunk_obj = {
            'file': os.path.basename(filepath),
            'file_path': rel_path,
            'chunk_id': idx,
            'content': chunk_text,
            'embedding': embedding,
            'metadata': {
                'file_path': rel_path,
                'title': doc_title,
                'section_title': section,
                'hierarchy': ' > '.join(hierarchy[:3]) if hierarchy else '',
                'last_modified': file_mtime_iso,
                'chunk_index': idx,
                'total_chunks_in_file': len(raw_chunks),
                'char_count': len(chunk_text),
                'keywords': simple_keywords(chunk_text),
            }
        }
        result_chunks.append(chunk_obj)

    return result_chunks


def show_stats():
    """显示向量数据库统计"""
    vectors_file = get_vectors_file()
    if not os.path.exists(vectors_file):
        print(f"[ERROR] 向量数据库不存在: {vectors_file}")
        print("[HINT] 请先运行: python embed_wiki.py")
        return

    with open(vectors_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    m = data.get('metadata', {})
    chunks = data.get('chunks', [])
    print("=" * 50)
    print("向量数据库统计")
    print("=" * 50)
    print(f"  模型:          {m.get('model', 'unknown')}")
    print(f"  总chunks:      {m.get('total_chunks', len(chunks))}")
    print(f"  构建时间:      {m.get('build_time', 'unknown')}")
    print(f"  版本:          {m.get('version', 'unknown')}")
    print(f"  切割策略:      {m.get('chunking_strategy', 'unknown')}")
    print(f"  文件数:        {len(data.get('file_hashes', {}))}")

    if chunks:
        lengths = [len(c['content']) for c in chunks]
        avg = sum(lengths) / len(lengths)
        short = sum(1 for l in lengths if l < 100)
        print(f"  平均长度:      {avg:.0f} 字符")
        print(f"  <100字符:      {short} ({short/len(chunks)*100:.1f}%)")
    print("=" * 50)


def main():
    if '--stats' in sys.argv:
        show_stats()
        return

    wiki_dir = Path(get_wiki_dir())
    vectors_file = get_vectors_file()
    embed_model = get_embed_model()

    if not wiki_dir.exists():
        print(f"[ERROR] 知识库目录不存在: {wiki_dir}")
        print("[HINT] 请检查 config.yaml 中的 wiki.dir 配置")
        sys.exit(1)

    print('=' * 60)
    print('LLM Wiki 向量化 v3.0')
    print(f'Wiki目录:   {wiki_dir}')
    print(f'输出文件:   {vectors_file}')
    print(f'嵌入模型:   {embed_model}')
    print('=' * 60)

    all_chunks = []
    file_hashes = {}
    md_files = list(wiki_dir.rglob('*.md'))

    print(f'发现 {len(md_files)} 个 .md 文件\n')

    for i, md_file in enumerate(md_files):
        rel = str(md_file.relative_to(wiki_dir))
        print(f'[{i+1}/{len(md_files)}] {rel}')

        file_hash = compute_file_hash(md_file)
        file_hashes[rel] = file_hash

        chunks = process_file(md_file, wiki_dir)
        all_chunks.extend(chunks)
        print(f'  累计: {len(all_chunks)} chunks\n')

    # 保存
    output = {
        'metadata': {
            'model': embed_model,
            'dimension': len(all_chunks[0]['embedding']) if all_chunks else 0,
            'build_time': datetime.now().isoformat(),
            'total_chunks': len(all_chunks),
            'version': '3.0',
            'chunking_strategy': 'markdown_semantic',
        },
        'file_hashes': file_hashes,
        'chunks': all_chunks,
    }

    os.makedirs(os.path.dirname(vectors_file), exist_ok=True)
    with open(vectors_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if all_chunks:
        lengths = [len(c['content']) for c in all_chunks]
        avg = sum(lengths) / len(lengths)
        short = sum(1 for l in lengths if l < 100)
        print('=' * 60)
        print('DONE!')
        print(f'  总chunks:    {len(all_chunks)}')
        print(f'  平均长度:    {avg:.0f} 字符')
        print(f'  <100字符:    {short} ({short/len(lengths)*100:.1f}%)')
        print(f'  输出:        {vectors_file}')
        print('=' * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[取消]')
    except Exception as e:
        import traceback
        print(f'CRASH: {e}')
        print(traceback.format_exc())
        sys.exit(1)
