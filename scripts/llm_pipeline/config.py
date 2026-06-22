from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    api_url: str
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4000
    # 注意：在 V4 中，chunk_size 的单位从字符升级为了真正的 Token 数
    chunk_size: int = 6000 
    workers: int = 3

def load_config(args) -> LLMConfig:
    """从命令行参数和环境变量中加载配置并实例化为 Dataclass"""
    base_url = args.base_url or os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    if base_url.endswith("/chat/completions"):
        api_url = base_url
    else:
        api_url = base_url.rstrip("/") + "/chat/completions"

    api_key = args.api_key or os.environ.get("LLM_API_KEY", "")
    if not api_key:
        raise RuntimeError("未提供 API Key，请设置环境变量 LLM_API_KEY 或使用 --api-key 参数")

    model = args.model or os.environ.get("LLM_MODEL", "Qwen/Qwen3-8B")

    return LLMConfig(
        api_url=api_url,
        api_key=api_key,
        model=model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        chunk_size=args.chunk_size,
        workers=args.workers
    )
