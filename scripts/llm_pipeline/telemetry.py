import sys

class TokenTelemetry:
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.api_calls = 0

    def record(self, prompt_tokens: int, completion_tokens: int):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.api_calls += 1

    def print_report(self):
        total = self.total_prompt_tokens + self.total_completion_tokens
        print("\n" + "="*45, file=sys.stderr)
        print("📊 [Token 消费与成本遥测财报 (Telemetry)]", file=sys.stderr)
        print("="*45, file=sys.stderr)
        print(f"  总请求次数   : {self.api_calls} 次", file=sys.stderr)
        print(f"  输入消耗     : {self.total_prompt_tokens} tokens", file=sys.stderr)
        print(f"  生成消耗     : {self.total_completion_tokens} tokens", file=sys.stderr)
        print(f"  共计消耗     : {total} tokens", file=sys.stderr)
        print("="*45 + "\n", file=sys.stderr)
