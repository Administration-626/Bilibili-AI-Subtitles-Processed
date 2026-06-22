import asyncio
import aiohttp
import re
from .engine import async_call_llm
from .prompts import SYSTEM_CHUNK_MAP, SYSTEM_TREE_REDUCE

def fix_markdown(text: str) -> str:
    """Markdown 语法纠错层"""
    # 仅统计行首的代码块标记，避免正文提到反引号导致误伤
    if len(re.findall(r"(?m)^```", text)) % 2 != 0:
        text += "\n```"
    return text

async def map_chunk(i: int, chunk: str, session: aiohttp.ClientSession, config, telemetry) -> tuple:
    """第一层：Map（局部特征提取）"""
    user_content = f"长文材料：第 {i+1} 块内容如下：\n\n```text\n{chunk}\n```"
    # 使用 override temperature，避免并发修改共享的 config 对象产生数据竞争
    partial = await async_call_llm(session, SYSTEM_CHUNK_MAP, user_content, config, telemetry, temperature=0.1)
    return i, f"【阶段 {i+1} 核心底层提要】:\n{partial}"

async def tree_reduce(partials: list, session: aiohttp.ClientSession, config, telemetry, sem: asyncio.Semaphore) -> str:
    """第二层核心：递归树状合并 (Tree Summarization) - 告别 Context 爆炸"""
    # 如果节点数少于等于4个，说明上下文安全，直接进入最终层
    if len(partials) <= 4:
        return "\n\n".join(partials)
        
    print(f"  [架构] 触发树状中间层归并 (Tree Reduce)，当前区块数：{len(partials)}...")
    
    # 每 4 个节点融合成 1 个超节点
    group_size = 4
    groups = [partials[i:i+group_size] for i in range(0, len(partials), group_size)]
    
    async def reduce_group(g: list, index: int) -> tuple:
        combined = "\n\n".join(g)
        user_content = f"请将以下几个连续的阶段性提要合并为一个结构连贯的长篇汇总。请务必保留关键论点、代码和具体数字：\n\n```text\n{combined}\n```"
        async with sem:
            res = await async_call_llm(session, SYSTEM_TREE_REDUCE, user_content, config, telemetry)
        return index, res
        
    tasks = [reduce_group(g, i) for i, g in enumerate(groups)]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    new_partials_with_index = []
    for i, res in enumerate(raw_results):
        if isinstance(res, Exception):
            print(f"  [警告] 树状合并中间层分组 {i+1} 失败，已跳过: {res}")
            continue
        new_partials_with_index.append(res)
        
    if not new_partials_with_index:
        raise RuntimeError("Tree Reduce 所有分支均失败，合并中止")
        
    new_partials_with_index.sort(key=lambda x: x[0])
    new_partials = [p[1] for p in new_partials_with_index]
    
    # 递归调用自己，直至归并结束
    return await tree_reduce(new_partials, session, config, telemetry, sem)

async def run_pipeline(text: str, chunks: list, system_prompt: str, config, telemetry) -> str:
    """主控管线"""
    async with aiohttp.ClientSession() as session:
        # 1. 文本极短，抄近道直达
        if len(chunks) == 1:
            print(f"  [节点] 文本长度安全，单次请求直达...")
            user_content = f"待整理材料如下：\n\n```text\n{text}\n```"
            result = await async_call_llm(session, system_prompt, user_content, config, telemetry)
            return fix_markdown(result)
            
        print(f"  [节点] 启动异步 Map 阶段 (共 {len(chunks)} 个高并发任务)...")
        # 并发控制器：限制一瞬间砸向 API 的请求数
        sem = asyncio.Semaphore(config.workers)
        
        async def bounded_map(i, chunk):
            async with sem:
                return await map_chunk(i, chunk, session, config, telemetry)
                
        tasks = [bounded_map(i, chunk) for i, chunk in enumerate(chunks)]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for i, res in enumerate(raw_results):
            if isinstance(res, Exception):
                print(f"  [警告] 第 {i+1} 块内容处理失败，已跳过以保护整体进度: {res}")
                continue
            results.append(res)
            
        if not results:
            raise RuntimeError("Map 阶段所有任务均失败，管线中止")
            
        results.sort(key=lambda x: x[0])
        partials = [p[1] for p in results]
        
        # 2. 启动树状归并
        final_partials_text = await tree_reduce(partials, session, config, telemetry, sem)
        
        # 3. 终结层
        print("  [节点] 输出最终顶层报告...")
        user_content = f"以下是经过层层提炼的完整结构材料。请你根据这些材料的综合信息，撰写并输出最终成稿：\n\n```text\n{final_partials_text}\n```"
        result = await async_call_llm(session, system_prompt, user_content, config, telemetry)
        
        return fix_markdown(result)
