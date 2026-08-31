# Delta CLI Architecture & System-Wide Refactor Design

**Date**: 2026-08-29  
**Status**: Approved  
**Author**: Delta Architecture Team  

---

## 1. Overview & Objectives

The goal of this refactor is a comprehensive architecture cleanup and stabilization of Delta CLI. The refactor unifies core execution paths, standardizes event-driven communication between CLI/TUI and Web UI, eliminates technical debt, and guarantees functional reliability across autonomous pentesting, AI agent logic, and web management interfaces.

---

## 2. Directory Structure & Module Boundaries

The codebase will be reorganized into 5 distinct, loosely-coupled packages:

```text
delta/
├── core/               # Central runtime, configuration, and event infrastructure
│   ├── __init__.py
│   ├── engine.py       # Central engine coordinator
│   ├── config.py       # App configuration loader
│   ├── session.py      # Active session tracker
│   ├── events.py       # Unified Pydantic event models & AsyncEventBus
│   ├── plugin.py       # Plugin interfaces & manager
│   ├── policy.py       # Execution security policy & guardrails
│   └── auth.py         # Authentication & RBAC helpers
├── ai/                 # Reasoning, Agent Loops & Tool Execution
│   ├── __init__.py
│   ├── llm.py          # Unified multi-provider LLM client
│   ├── react_loop.py   # ReAct reasoning and execution loop
│   ├── tools.py        # Dynamic tool registration & schema generation
│   ├── memory.py       # Conversation history & context manager
│   ├── reasoning.py    # Intent parsing & chain-of-thought processing
│   └── context.py      # Context window builder
├── pentest/            # Autonomous Penetration Testing Subsystem
│   ├── __init__.py
│   ├── orchestrator.py # Multi-phase pentest pipeline controller
│   ├── metasploit.py   # MSFRPC REST/RPC API client interface
│   ├── burp.py         # Burp Suite REST API integration wrapper
│   ├── risk.py         # Vulnerability scoring & severity matrix
│   ├── evidence.py     # Proof-of-Concept & evidence logger
│   └── scope.py        # Target boundary & scope enforcer
├── web/                # Web UI Server & WebSocket Gateway
│   ├── __init__.py
│   ├── server.py       # FastAPI application entrypoint
│   ├── bridge.py       # AsyncEventBus <-> WebSocket relay
│   └── static/         # Web dashboard frontend assets
└── modules/            # Standalone Utility & Execution Modules
    ├── __init__.py
    ├── network.py      # Port scanning & network probes
    ├── websearch.py    # OSINT & search integration
    ├── bruteforce.py   # Credential testing logic
    ├── crypto.py       # Hashing & encoding utilities
    └── terminal.py     # Local shell execution wrapper
```

### Cleanup Rules:
1. Delete redundant/outdated backup files (`delta/ai/llm.py.bak`).
2. Consolidate event models into `delta/core/events.py` (deprecating duplicate `delta/ai/events.py`).

---

## 3. Communication Architecture (Async Event Bus)

All subsystem actions, findings, and tool updates emit typed events through `AsyncEventBus`.

```text
  [ Pentest Orchestrator / ReAct Loop ]
                    │
                    ▼ (Publishes Events)
             AsyncEventBus (`delta/core/events.py`)
             ├──► CLI/TUI Renderer (Local Terminal Stream)
             └──► Web UI Bridge (`delta/web/bridge.py`) ──WebSocket──► Web Dashboard
```

### Key Event Types:
* `SystemStateEvent`: Engine state changes (INIT, RUNNING, PAUSED, FINISHED).
* `AgentStepEvent`: ReAct thought, action, and observation steps.
* `ToolExecutionEvent`: Tool call arguments and raw outputs.
* `FindingDiscoveredEvent`: Vulnerability findings, severity, evidence.
* `LogEvent`: Diagnostic and system logs.

---

## 4. Subsystem Stabilizations

### A. Autonomous Pentest Subsystem (`delta/pentest/`)
* **Metasploit Integration (`metasploit.py`)**: Safe client initialization; gracefully surfaces connection errors if MSFRPC daemon is unreachable.
* **Burp Suite Integration (`burp.py`)**: Connects to Burp REST API for target ingestion, scanning, and issue extraction.
* **Scope Enforcer (`scope.py`)**: Strict target validation preventing out-of-scope interactions.
* **Orchestrator (`orchestrator.py`)**: Manages multi-phase state (Recon -> Scan -> Exploit -> Report) with evidence tracking.

### B. AI Reasoning Engine (`delta/ai/`)
* Standardize tool JSON schema generation in `delta/ai/tools.py`.
* Ensure `delta/ai/react_loop.py` correctly handles tool execution failures without breaking loop iteration.

### C. Web Server & Interface (`delta/web/`)
* Ensure FastAPI server runs reliably via Uvicorn.
* Synchronize WebSocket bridge (`bridge.py`) state with active session events.

---

## 5. Verification & Testing Strategy

1. **Unit Tests**:
   * Event Bus pub-sub functionality (`tests/test_core_events.py`).
   * Metasploit & Burp RPC fallback handling (`tests/test_pentest_integrations.py`).
   * Tool schema generation & execution (`tests/test_ai_tools.py`).
2. **Integration Verification**:
   * Execution of CLI engine smoke test (`python -m delta --help` and `--version`).
   * Web server startup and WebSocket connection test (`python -m delta web`).
