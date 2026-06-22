import asyncio
import aiohttp
import sys

async def async_call_llm(session: aiohttp.ClientSession, system_prompt: str, user_content: str, config, telemetry, temperature: float = None) -> str:
    """全异步底层发包引擎（带自适应并发退避与遥测埋点）"""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature if temperature is not None else config.temperature,
    }
    if config.max_tokens > 0:
        payload["max_tokens"] = config.max_tokens

    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            async with session.post(config.api_url, headers=headers, json=payload, timeout=300) as resp:
                if resp.status == 401:
                    raise RuntimeError(f"HTTP 401 (API Key 无效或未授权)")
                if resp.status in (429, 502, 503, 504):
                    raise RuntimeError(f"HTTP {resp.status} (节点过载或限流)")
                resp.raise_for_status()
                
                data = await resp.json()
                
                # 记录 Token 遥测数据
                usage = data.get("usage", {})
                if usage:
                    telemetry.record(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    )
                
                choices = data.get("choices")
                if not choices or not isinstance(choices, list):
                    raise ValueError(f"API 返回无效的 choices: {data}")
                choice = choices[0]
                if not isinstance(choice, dict):
                    raise ValueError(f"API 返回无效的 choice 结构: {choice}")
                message = choice.get("message")
                if not isinstance(message, dict):
                    raise ValueError(f"API 返回无效的 message 结构: {message}")
                content = message.get("content")
                if not content:
                    raise ValueError("API 返回的数据体为空 (Empty content)")
                return content
                
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"  [致命错误] 网络请求彻底失败，放弃重试: {e}", file=sys.stderr)
                raise
            
            # 自适应退避：如果遇到 429 限流，等待时间加倍
            wait_time = (2 ** attempt) * (2 if "429" in str(e) else 1)
            print(f"  [引擎] 异步请求受阻 (尝试 {attempt+1}/{max_attempts})，等待 {wait_time}s 回拨重试: {e}", file=sys.stderr)
            await asyncio.sleep(wait_time)
