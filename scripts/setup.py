#!/usr/bin/env python3
"""
配置向导 - 首次运行引导
- 交互式生成 config.yaml
- 可选启用RAG模块
- 创建知识库目录结构

用法:
  python setup.py                  # 首次配置
  python setup.py --enable-rag     # 启用RAG（已配置过的情况下）
  python setup.py --reset          # 重新配置（覆盖现有config）
"""

import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "config.yaml"
TEMPLATE_CONFIG = SCRIPT_DIR.parent / "templates" / "config.yaml.example"


def check_dependencies():
    """检查并安装Python依赖"""
    required = {'requests': 'requests', 'numpy': 'numpy'}
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print("[依赖检查] 缺少以下Python包:", ", ".join(missing))
        try:
            install = input("是否现在安装？ [Y/n]: ").strip().lower()
            if install != 'n':
                req_file = SCRIPT_DIR.parent / "requirements.txt"
                print(f"正在安装依赖...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
                print("[OK] 依赖安装完成")
            else:
                print("[WARN] 未安装依赖，RAG功能将无法使用")
                print(f"  手动安装: pip install -r {SCRIPT_DIR.parent / 'requirements.txt'}")
        except Exception as e:
            print(f"[ERROR] 安装失败: {e}")
            print(f"  手动安装: pip install -r {SCRIPT_DIR.parent / 'requirements.txt'}")


def read_input(prompt, default=None):
    """读取用户输入，支持默认值"""
    suffix = f" [{default}]" if default else ""
    user_input = input(f"{prompt}{suffix}: ").strip()
    return user_input if user_input else (default or "")


def read_yes_no(prompt, default=True):
    """读取是/否"""
    default_str = "Y/n" if default else "y/N"
    user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not user_input:
        return default
    return user_input in ('y', 'yes', '是')


def create_wiki_structure(wiki_dir):
    """创建知识库目录结构"""
    wiki_dir = Path(wiki_dir)
    dirs = [
        "",  # 根目录
        "projects",
        "org",
        "org/meetings",
        "org/policies",
        "org/members",
        "methods",
        "cases",
        "resources",
        "daily",
        "archive",
    ]
    for d in dirs:
        (wiki_dir / d).mkdir(parents=True, exist_ok=True)

    # 创建占位文件
    readme = wiki_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# 知识库\n\n"
            "> 本目录是组织知识库根目录\n\n"
            "## 目录结构\n\n"
            "| 目录 | 用途 |\n|------|------|\n"
            "| projects/ | 项目知识 |\n"
            "| org/ | 组织内部（会议/制度/成员） |\n"
            "| methods/ | 方法论/工具 |\n"
            "| cases/ | 案例库 |\n"
            "| resources/ | 外部资源 |\n"
            "| daily/ | 日常工作记录 |\n"
            "| archive/ | 归档（过时文档） |\n",
            encoding='utf-8'
        )

    # 复制三层索引模板
    index_template = SCRIPT_DIR.parent / "templates" / "knowledge_index.md"
    index_file = wiki_dir / "knowledge_index.md"
    if index_template.exists() and not index_file.exists():
        index_file.write_text(index_template.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"  [CREATE] {index_file}")


def check_ollama():
    """检查Ollama是否可用"""
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            return True, model_names
    except:
        pass
    return False, []


def setup_rag():
    """配置RAG模块"""
    print("\n" + "=" * 50)
    print("RAG 模块配置")
    print("=" * 50)

    print("\nRAG模块需要Ollama（本地AI运行环境）。")
    print("Ollama 允许在本机运行AI模型，数据不外传。")
    print("下载地址: https://ollama.com/download\n")

    ollama_ok, models = check_ollama()
    if ollama_ok:
        print(f"[OK] 检测到Ollama运行中")
        print(f"  已安装模型: {', '.join(models) if models else '无'}")

        # 检查必要模型
        has_embed = any('nomic-embed' in m for m in models)
        has_gen = any('qwen' in m or 'llama' in m for m in models)

        if not has_embed:
            print("\n[WARN] 未检测到嵌入模型 nomic-embed-text")
            print("  需要下载: ollama pull nomic-embed-text (约274MB)")
            if read_yes_no("  是否现在下载？", default=False):
                os.system("ollama pull nomic-embed-text")

        if not has_gen:
            print("\n[WARN] 未检测到生成模型")
            print("  推荐: ollama pull qwen2.5:7b (约4.7GB)")
            print("  或轻量: ollama pull qwen2:1.5b (约934MB)")
            if read_yes_no("  是否现在下载 qwen2.5:7b？", default=False):
                os.system("ollama pull qwen2.5:7b")
    else:
        print("[WARN] 未检测到Ollama运行")
        print("  请先安装Ollama: https://ollama.com/download")
        print("  安装后运行: ollama serve")
        if not read_yes_no("\n  是否跳过RAG配置，稍后再启用？", default=True):
            return False

    return True


def generate_config(wiki_dir, rag_enabled, rag_config=None):
    """生成config.yaml"""
    rag_config = rag_config or {}

    config_content = f"""# 组织知识库配置文件
# 由 setup.py 自动生成，也可手动编辑

# === 知识库核心配置 ===
wiki:
  # 知识库根目录（存放 .md 文件的目录）
  dir: {wiki_dir}

  # 三层索引文件（相对 wiki.dir 的路径）
  index_file: knowledge_index.md

# === RAG 配置（可选模块）===
rag:
  # 是否启用 RAG
  enabled: {str(rag_enabled).lower()}

  # 向量数据库存储路径
  vectors_dir: {rag_config.get('vectors_dir', './rag-data')}

  # 向量数据库文件名
  vectors_file: wiki_vectors.json

  # Ollama API 地址
  ollama_api: {rag_config.get('ollama_api', 'http://localhost:11434')}

  # 嵌入模型
  embed_model: {rag_config.get('embed_model', 'nomic-embed-text')}

  # 生成模型
  gen_model: {rag_config.get('gen_model', 'qwen2.5:7b')}

  # 检索返回的相关段落数量
  top_k: 5

  # Chunk 切割参数
  chunk_min_len: 150
  chunk_max_len: 400
  chunk_table_max: 600

# === 维护配置 ===
maintenance:
  archive_dir: archive/
  log_dir: ./logs
"""
    CONFIG_FILE.write_text(config_content, encoding='utf-8')
    print(f"\n[CREATE] 配置文件已生成: {CONFIG_FILE}")


def main():
    print("=" * 60)
    print("组织知识库 - 配置向导")
    print("=" * 60)

    # 依赖检查
    check_dependencies()

    # 检查是否已配置
    if CONFIG_FILE.exists() and '--reset' not in sys.argv:
        if '--enable-rag' in sys.argv:
            print("\n检测到现有配置，将启用RAG模块...")
            # 读取现有配置，修改rag.enabled
            content = CONFIG_FILE.read_text(encoding='utf-8')
            # 简单替换
            content = content.replace('enabled: false', 'enabled: true')
            CONFIG_FILE.write_text(content, encoding='utf-8')

            if setup_rag():
                print("[OK] RAG已启用")
            else:
                # 回退
                content = content.replace('enabled: true', 'enabled: false')
                CONFIG_FILE.write_text(content, encoding='utf-8')
                print("[CANCEL] RAG未启用")
            return

        print(f"\n[INFO] 配置文件已存在: {CONFIG_FILE}")
        print("  如需重新配置，请运行: python setup.py --reset")
        return

    print("\n本向导将帮你完成：")
    print("  1. 设置知识库目录")
    print("  2. 创建目录结构")
    print("  3. （可选）配置RAG模块\n")

    # 1. 知识库目录
    default_dir = str(SCRIPT_DIR.parent / "my-wiki")
    wiki_dir = read_input("\n[1/3] 知识库根目录路径", default=default_dir)
    wiki_dir = str(Path(wiki_dir).resolve())

    print(f"\n  将在 {wiki_dir} 创建知识库目录结构...")
    create_wiki_structure(wiki_dir)
    print(f"  [OK] 目录结构已创建")

    # 2. 是否启用RAG
    print("\n" + "-" * 50)
    print("[2/3] RAG模块（可选）")
    print("-" * 50)
    print("\nRAG = 让AI参考你的知识库回答问题")
    print("  - 需要: Ollama + 本地AI模型（约5GB磁盘空间）")
    print("  - 好处: 数据隐私、零API成本、离线可用")
    print("  - 适合: 知识库>50篇文档，或需要AI问答\n")

    rag_enabled = read_yes_no("是否现在配置RAG？", default=False)

    rag_config = {
        'vectors_dir': str(SCRIPT_DIR.parent / "rag-data"),
        'ollama_api': 'http://localhost:11434',
        'embed_model': 'nomic-embed-text',
        'gen_model': 'qwen2.5:7b',
    }

    if rag_enabled:
        if setup_rag():
            print("[OK] RAG配置完成")
        else:
            rag_enabled = False
            print("[INFO] RAG未配置，可稍后运行: python setup.py --enable-rag")

    # 3. 生成配置
    print("\n" + "-" * 50)
    print("[3/3] 生成配置文件")
    print("-" * 50)
    generate_config(wiki_dir, rag_enabled, rag_config)

    # 完成
    print("\n" + "=" * 60)
    print("配置完成！")
    print("=" * 60)
    print(f"\n知识库目录: {wiki_dir}")
    print(f"配置文件:   {CONFIG_FILE}")
    print(f"RAG状态:    {'已启用' if rag_enabled else '未启用（可稍后运行 setup.py --enable-rag）'}")

    print("\n下一步:")
    print(f"  1. 在 {wiki_dir} 下按标准编写 .md 文档")
    print(f"  2. 参考 knowledge_index.md 模板建立三层索引")
    if rag_enabled:
        print(f"  3. 运行向量化: cd {SCRIPT_DIR} && python embed_wiki.py")
        print(f"  4. 查询: python agentic_rag.py '你的问题'")
    print(f"\n详细文档见: {SCRIPT_DIR.parent / 'SKILL.md'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n[取消配置]')
    except Exception as e:
        import traceback
        print(f'ERROR: {e}')
        print(traceback.format_exc())
        sys.exit(1)
