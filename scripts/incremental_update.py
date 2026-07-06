#!/usr/bin/env python3
"""
增量向量化脚本 v1.0（通用版）
- 只重新向量化修改过/新增的.md文件
- 从向量数据库读取已有数据，只更新变化部分
- 配置从 config.yaml 读取

用法:
  python incremental_update.py           # 增量更新
  python incremental_update.py --full    # 全量重建
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import get_wiki_dir, get_vectors_file, get_embed_model

# 复用 embed_wiki 的切割和向量化逻辑
from embed_wiki import (
    split_markdown_semantic, merge_short_chunks, get_embedding,
    extract_title, simple_keywords, compute_file_hash
)


def load_db():
    """加载现有向量数据库"""
    vectors_file = get_vectors_file()
    if not os.path.exists(vectors_file):
        return None, {}, []
    with open(vectors_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data, data.get('file_hashes', {}), data.get('chunks', [])


def save_db(data):
    """保存向量数据库"""
    vectors_file = get_vectors_file()
    os.makedirs(os.path.dirname(vectors_file), exist_ok=True)
    with open(vectors_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] {vectors_file}")


def embed_file(filepath, wiki_dir):
    """向量化单个文件，返回 chunks 列表"""
    rel_path = str(Path(filepath).relative_to(wiki_dir))
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERR] 读取失败: {e}")
        return []

    raw_chunks = split_markdown_semantic(content)
    raw_chunks = merge_short_chunks(raw_chunks)
    print(f"  -> {len(raw_chunks)} chunks")

    doc_title = extract_title(content)
    file_mtime = os.path.getmtime(filepath)
    file_mtime_iso = datetime.fromtimestamp(file_mtime).isoformat()

    result = []
    for idx, chunk_text in enumerate(raw_chunks):
        emb = get_embedding(chunk_text)
        if emb is None:
            continue
        chunk_obj = {
            'file': os.path.basename(filepath),
            'file_path': rel_path,
            'chunk_id': idx,
            'content': chunk_text,
            'embedding': emb,
            'metadata': {
                'file_path': rel_path,
                'title': doc_title,
                'section_title': chunk_text.split('\n')[0][:80],
                'hierarchy': '',
                'last_modified': file_mtime_iso,
                'chunk_index': idx,
                'total_chunks_in_file': len(raw_chunks),
                'char_count': len(chunk_text),
                'keywords': simple_keywords(chunk_text),
            }
        }
        result.append(chunk_obj)
    return result


def incremental_update():
    """增量更新主函数"""
    wiki_dir = Path(get_wiki_dir())

    if not wiki_dir.exists():
        print(f"[ERROR] 知识库目录不存在: {wiki_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("增量向量化 v1.0")
    print(f"{'='*60}\n")

    data, old_hashes, old_chunks = load_db()

    md_files = list(wiki_dir.rglob('*.md'))

    # 扫描文件变化
    current_hashes = {}
    modified = []
    new = []

    for mf in md_files:
        rel = str(mf.relative_to(wiki_dir))
        h = compute_file_hash(mf)
        current_hashes[rel] = h
        if rel not in old_hashes:
            new.append((mf, rel, h))
        elif old_hashes[rel] != h:
            modified.append((mf, rel, h))

    # 检测删除的文件
    deleted = [rel for rel in old_hashes if rel not in current_hashes]

    print(f"文件扫描: {len(md_files)} 个 .md")
    print(f"  新增: {len(new)}")
    print(f"  修改: {len(modified)}")
    print(f"  删除: {len(deleted)}")
    print()

    if not new and not modified and not deleted:
        print("[OK] 没有文件变化，无需更新")
        return

    # 删除旧 chunks
    rels_to_remove = set(rel for _, rel, _ in new + modified) | set(deleted)
    filtered_chunks = [
        c for c in old_chunks
        if c.get('metadata', {}).get('file_path', c.get('file_path', '')) not in rels_to_remove
    ]

    print(f"移除旧 chunks: {len(old_chunks)} -> {len(filtered_chunks)}")

    # 重新向量化
    new_chunks = []
    for mf, rel, h in new + modified:
        print(f"\n[处理] {rel}")
        chunks = embed_file(mf, wiki_dir)
        new_chunks.extend(chunks)
        current_hashes[rel] = h

    all_chunks = filtered_chunks + new_chunks

    # 保存
    if data is None:
        data = {}
    data['metadata'] = {
        'model': get_embed_model(),
        'dimension': len(all_chunks[0]['embedding']) if all_chunks else 0,
        'build_time': datetime.now().isoformat(),
        'total_chunks': len(all_chunks),
        'version': data.get('metadata', {}).get('version', '3.0'),
        'chunking_strategy': 'markdown_semantic_incremental',
    }
    data['file_hashes'] = current_hashes
    data['chunks'] = all_chunks

    save_db(data)

    if all_chunks:
        lens = [len(c['content']) for c in all_chunks]
        avg = sum(lens) / len(lens)
        short = sum(1 for l in lens if l < 100)
        print(f"\n{'='*60}")
        print("DONE!")
        print(f"  总chunks:    {len(all_chunks)}")
        print(f"  平均长度:    {avg:.0f} 字符")
        print(f"  <100字符:    {short} ({short/len(lens)*100:.1f}%)")
        print(f"{'='*60}")


if __name__ == '__main__':
    try:
        if '--full' in sys.argv:
            print("[FULL] 全量重建模式")
            from embed_wiki import main
            main()
        else:
            incremental_update()
    except KeyboardInterrupt:
        print('\n[取消]')
    except Exception as e:
        import traceback
        print(f'CRASH: {e}')
        print(traceback.format_exc())
        sys.exit(1)
