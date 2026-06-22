#!/usr/bin/env python3
"""
入口包装器：将旧版本的独立脚本请求转发到 V4 包引擎
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm_pipeline.cli import main

if __name__ == "__main__":
    main()
