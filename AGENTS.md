# Delta CLI - AGENTS Instructions



This project is Delta, an AI-powered Cyber Security Assessment CLI integrated with Ollama Qwen 3.6.



## LLM Configuration

- **Provider**: Ollama (local)

- **Model**: Qwen 3.6 (`qwen3.6`)

- **Base URL**: `http://localhost:11434/v1`

- **API Key**: Not required (local Ollama)



## How to use

1. Ensure Ollama is running: `ojllama serve`

2. Pull the model: `ollama pull qwen3.6` (or the appropriate tag for your Ollama installation)

3. Start Delta: `python -m delta` or `delta`



## Switching models

Inside Delta REPL:

- `/model qwen3.6` - Switch to Qwen 3.6

- `/model qwen3` - Switch to Qwen 3

- `/model qwen2.5` - Switch to Qwen 2.5

- `/model qwen2.5:3b` - Switch to Qwen 2.5 3B

- `/provider local` - Ensure Ollama provider is active