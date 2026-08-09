import subprocess
import re

# Get original from git
result = subprocess.run(['git', 'show', 'HEAD:delta/ai/llm.py'],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
orig = result.stdout

# Fix 1: add import from protocols
orig = orig.replace(
    'from delta.ai.memory import MemoryManager\n',
    'from delta.ai.memory import MemoryManager\nfrom delta.ai.protocols import MODEL_PRESETS\n'
)

# Fix 2: add re-export block after imports
orig = orig.replace(
    'PROVIDERS = {',
    '__all__ = ["LLMEngine", "parse_command_from_response", "strip_command_tags", "PROVIDERS", "MODEL_PRESETS"]\n\nPROVIDERS = {',
    1  # only first occurrence
)

# Fix 3: change default_model from naxxcombo to KiloCombo in 9router provider
orig = orig.replace(
    '"default_model": "naxxcombo",',
    '"default_model": "KiloCombo",',
    1
)

# Fix 4: add KiloCombo preset to MODEL_PRESETS
orig = orig.replace(
    '"description": "NaxxCombo model on 9Router",',
    '"description": "NaxxCombo model on 9Router",\n    },\n    "KiloCombo": {\n        "model": "KiloCombo",\n        "base_url": "http://localhost:20128/v1",\n        "provider": "9router",\n        "description": "KiloCombo model on 9Router (Advanced model with superior coding capabilities)",\n    },',
    1
)

with open('delta/ai/llm.py', 'w', encoding='utf-8') as f:
    f.write(orig)

print('Fixed llm.py')
