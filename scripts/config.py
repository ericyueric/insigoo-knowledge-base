#!/usr/bin/env python3
"""
配置加载器 - 从 config.yaml 读取配置
所有脚本共用此模块加载配置
"""

import os
import sys
from pathlib import Path

CONFIG_FILE = "config.yaml"


def get_config_path():
    """查找 config.yaml（当前目录 → 脚本目录 → 上级目录）"""
    candidates = [
        CONFIG_FILE,
        str(Path(__file__).parent / CONFIG_FILE),
        str(Path(__file__).parent.parent / CONFIG_FILE),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def parse_simple_yaml(text):
    """简单YAML解析器（无需PyYAML依赖，支持两级嵌套）"""
    config = {}
    current_section = None
    for line in text.split('\n'):
        line = line.rstrip()
        if not line or line.strip().startswith('#'):
            continue
        # 顶级 section（如 wiki:, rag:）
        if not line.startswith(' ') and line.endswith(':'):
            current_section = line[:-1].strip()
            config[current_section] = {}
        # section 下的键值对
        elif current_section and line.startswith('  ') and not line.startswith('   '):
            stripped = line.strip()
            if ':' in stripped:
                key, _, value = stripped.partition(':')
                key = key.strip()
                value = value.strip()
                # 去除行内注释
                if '#' in value:
                    value = value.split('#')[0].strip()
                # 去除引号
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # 类型转换
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.lstrip('-').isdigit():
                    value = int(value)
                config[current_section][key] = value
    return config


def load_config():
    """加载配置，优先用PyYAML，失败则用内置解析器"""
    config_path = get_config_path()
    if not config_path:
        print("[ERROR] 找不到 config.yaml")
        print("[HINT] 请先运行: python setup.py")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        text = f.read()

    try:
        import yaml
        config = yaml.safe_load(text) or {}
    except ImportError:
        config = parse_simple_yaml(text)

    return config


def get_wiki_dir():
    """获取知识库根目录（绝对路径）"""
    config = load_config()
    wiki_dir = config.get('wiki', {}).get('dir', './my-wiki')
    return str(Path(wiki_dir).resolve())


def get_rag_config():
    """获取RAG配置"""
    config = load_config()
    return config.get('rag', {})


def get_vectors_file():
    """获取向量数据库文件完整路径"""
    config = load_config()
    rag = config.get('rag', {})
    vectors_dir = rag.get('vectors_dir', './rag-data')
    vectors_file = rag.get('vectors_file', 'wiki_vectors.json')
    return str(Path(vectors_dir).resolve() / vectors_file)


def get_ollama_api(endpoint='embeddings'):
    """获取Ollama API地址"""
    config = load_config()
    rag = config.get('rag', {})
    base = rag.get('ollama_api', 'http://localhost:11434')
    return f"{base}/api/{endpoint}"


def get_embed_model():
    return get_rag_config().get('embed_model', 'nomic-embed-text')


def get_gen_model():
    return get_rag_config().get('gen_model', 'qwen2.5:7b')


def get_top_k():
    return int(get_rag_config().get('top_k', 5))


def get_chunk_params():
    """获取chunk切割参数"""
    rag = get_rag_config()
    return {
        'min_len': int(rag.get('chunk_min_len', 150)),
        'max_len': int(rag.get('chunk_max_len', 400)),
        'table_max': int(rag.get('chunk_table_max', 600)),
    }


if __name__ == '__main__':
    config = load_config()
    print("=" * 50)
    print("当前配置")
    print("=" * 50)
    print(f"  Wiki目录:    {get_wiki_dir()}")
    print(f"  RAG启用:     {config.get('rag', {}).get('enabled', False)}")
    if config.get('rag', {}).get('enabled'):
        print(f"  向量数据库:  {get_vectors_file()}")
        print(f"  嵌入模型:    {get_embed_model()}")
        print(f"  生成模型:    {get_gen_model()}")
        print(f"  Top-K:       {get_top_k()}")
    print(f"  配置文件:    {get_config_path()}")
