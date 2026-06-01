"""下载 cross-encoder 重排序模型到本地（通过 ModelScope）"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LOCAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "models", "cross-encoder__ms-marco-MiniLM-L-6-v2")

def download_via_modelscope():
    """通过 ModelScope 下载模型"""
    from modelscope import snapshot_download
    # ModelScope 上的对应模型
    model_id = "iic/nlp_corom_passage-ranking_english-base"
    print(f"正在从 ModelScope 下载 {model_id} ...")
    local_path = snapshot_download(model_id)
    print(f"已下载到: {local_path}")
    return local_path

def download_via_hf_mirror():
    """通过 HF 镜像下载"""
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from sentence_transformers import CrossEncoder
    print(f"正在从 HF 镜像下载 {MODEL_NAME} ...")
    model = CrossEncoder(MODEL_NAME, device="cpu")
    # 保存到本地目录
    model.save(LOCAL_DIR)
    print(f"已保存到: {LOCAL_DIR}")

def download_via_modelscope_hub():
    """通过 modelscope hub 下载 HuggingFace 模型"""
    from modelscope.hub.snapshot_download import snapshot_download
    model_id = "sentence-transformers/ms-marco-MiniLM-L-6-v2"
    print(f"正在从 ModelScope Hub 下载 {model_id} ...")
    local_path = snapshot_download(model_id)
    print(f"已下载到: {local_path}")
    # 检查是否下载成功
    if os.path.isdir(local_path):
        # 创建符号链接或复制到目标目录
        print(f"模型文件: {os.listdir(local_path)}")
    return local_path

if __name__ == "__main__":
    if os.path.isdir(LOCAL_DIR):
        print(f"模型已存在于: {LOCAL_DIR}")
        sys.exit(0)

    print(f"目标目录: {LOCAL_DIR}")
    print("尝试多种下载方式...\n")

    # 方式1：HF 镜像
    try:
        download_via_hf_mirror()
        sys.exit(0)
    except Exception as e:
        print(f"  HF 镜像失败: {e}")

    # 方式2：ModelScope Hub
    try:
        path = download_via_modelscope_hub()
        os.makedirs(os.path.dirname(LOCAL_DIR), exist_ok=True)
        # 复制到目标目录
        import shutil
        if path != LOCAL_DIR:
            shutil.copytree(path, LOCAL_DIR, dirs_exist_ok=True)
        print(f"已复制到: {LOCAL_DIR}")
        sys.exit(0)
    except Exception as e:
        print(f"  ModelScope Hub 失败: {e}")

    print("\n所有下载方式均失败。请手动下载模型并放置到:")
    print(f"  {LOCAL_DIR}")
    print("模型地址: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2")
