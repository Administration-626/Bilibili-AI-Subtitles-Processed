import sys
try:
    import tiktoken
except ImportError:
    print("错误: 缺少 tiktoken 模块，请先运行: pip install tiktoken", file=sys.stderr)
    sys.exit(1)

def get_tokenizer(model_name: str = "cl100k_base"):
    try:
        return tiktoken.get_encoding(model_name)
    except Exception:
        if model_name != "cl100k_base":
            return tiktoken.get_encoding("cl100k_base")
        raise Exception("无法初始化分词器")

def count_tokens(text: str, tokenizer) -> int:
    return len(tokenizer.encode(text, disallowed_special=()))

def chunk_text_by_tokens(text: str, max_tokens: int, tokenizer) -> list:
    """基于真实 Token 算力边界的精确语义切分"""
    paragraphs = text.split("\n\n")
    if len(paragraphs) == 1:
        paragraphs = text.split("\n")

    chunks = []
    current_chunk = []
    current_tokens = 0

    newline_tokens = count_tokens("\n\n", tokenizer)

    for p in paragraphs:
        p_tokens = count_tokens(p, tokenizer)
        
        # 极端情况：单个段落自身 Token 已经超限
        if p_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # 对超大段落进行降级硬切，确保不引发 context exceeded
            char_step = max(1, int(len(p) * (max_tokens / p_tokens) * 0.9))
            start = 0
            while start < len(p):
                chunks.append(p[start:start+char_step])
                start += char_step
            continue
            
        if current_tokens + p_tokens > max_tokens:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_tokens = p_tokens
        else:
            current_chunk.append(p)
            current_tokens += p_tokens + newline_tokens
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks
