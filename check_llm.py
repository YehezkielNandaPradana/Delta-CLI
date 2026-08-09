import re

with open('delta/ai/llm.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find 9router provider and check default_model
match = re.search(r'"9router":.*?"default_model":\s*"([^"]+)"', content, re.DOTALL)
if match:
    print(f'9Router default_model is: {match.group(1)}')
else:
    print('Could not find 9Router default_model')

# Check if KiloCombo is in MODEL_PRESETS
if '"KiloCombo":' in content:
    print('KiloCombo is present in MODEL_PRESETS')
else:
    print('KiloCombo is NOT in MODEL_PRESETS')

# List all MODEL_PRESETS entries
import json
# Simple approach: find all keys in MODEL_PRESETS
keys = re.findall(r'"([^"]+)":\s*{', content)
print(f'\nFound MODEL_PRESETS keys: {keys}')

# Check for naxxcombo
if 'naxxcombo' in content.lower():
    print('naxxcombo is still in MODEL_PRESETS')
else:
    print('naxxcombo is NOT in MODEL_PRESETS')
