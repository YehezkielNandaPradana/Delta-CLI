import json

# Read current kilo.json
with open('kilo.json', 'r') as f:
    data = json.load(f)

# Add 9router provider to enabled_providers if not present
if '9router' not in data.get('enabled_providers', []):
    data['enabled_providers'].append('9router')

# Update the provider section to include 9router
if 'provider' not in data:
    data['provider'] = {}

# Add 9router provider config
data['provider']['9router'] = {
    "options": {
        "baseURL": "http://localhost:20128/v1",
        "timeout": 120000
    },
    "models": {
        "KiloCombo": {
            "name": "KiloCombo (9Router)"
        }
    },
    "requires_key": False
}

# Update the model to use KiloCombo
if '9router' in data.get('provider', {}):
    # Check if KiloCombo model should be the default
    if 'model' in data and 'ollama/gemma4:12b' in data['model']:
        # Update default model to KiloCombo (assuming it should use 9Router)
        data['model'] = "KiloCombo"
        data['small_model'] = "KiloCombo"

# Write back to kilo.json
with open('kilo.json', 'w') as f:
    json.dump(data, f, indent=2)

print("kilo.json updated successfully")
print(f"Enabled providers: {data.get('enabled_providers', [])}")
print(f"Default model: {data.get('model')}")
print(f"Provider section keys: {list(data.get('provider', {}).keys())}")
