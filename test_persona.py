import os
import sys

# Try new google-genai SDK first
try:
    import google.genai as genai
    from google.genai import types
    has_new_sdk = True
except ImportError:
    has_new_sdk = False
    import google.generativeai as old_genai

with open("Xiaofan_Knowledge_Distillation/Prompt_System.md", 'r', encoding='utf-8') as f:
    system_prompt = f.read()

question = '【弹幕提问】：范总，我看到有人说最近全面强制交社保的新规，其实有反内卷的意思。就是把那些付不起社保的、靠低成本人力的落后产能和小微企业淘汰掉，这样留下来的企业做出来的产品都能卖个好价钱，整体经济就会好起来。你觉得这么理解对吗？'

print("QUESTION:", question)
print("-" * 40)

if has_new_sdk:
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )
    )
    print(response.text)
else:
    old_genai.configure()
    model = old_genai.GenerativeModel(
        'gemini-2.5-pro',
        system_instruction=system_prompt
    )
    response = model.generate_content(question)
    print(response.text)
