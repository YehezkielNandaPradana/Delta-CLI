# Refactor: chat handler
"""
Delta Web Chat Interface

Web-based chat interface that integrates with the Delta CLI system,
featuring the manja toxic female AI personality with Delta's security expertise.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from flask import Flask, render_template_string, request, jsonify, session
    import markdown
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False

if not _FLASK_AVAILABLE:
    raise ImportError("Flask is required for web UI. Install with: pip install flask")

from delta.core.config import DeltaConfig
from delta.core.engine import DeltaEngine
from delta.core.display import DisplayManager
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.ai.intent import IntentEngine
from delta.ai.llm import LLMEngine

# HTML Template for the chat interface with Delta's distinctive styling
CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Delta - AI Security Chat</title>
    <style>
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2235;
            --bg-card-hover: #1f2a40;
            --accent-green: #00ff88;
            --accent-cyan: #00d4ff;
            --accent-purple: #a855f7;
            --accent-red: #ff4466;
            --accent-yellow: #ffcc00;
            --accent-orange: #ff8800;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #1e293b;
            --border-active: #334155;
            --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
            --font-sans: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            --radius: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --shadow: 0 4px 24px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 40px rgba(0,0,0,0.5);
            --transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        }
        html {
            scroll-behavior: smooth;
            font-size: 16px;
            height: 100%;
        }
        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(10,14,23,0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            transition: var(--transition);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--text-primary);
            text-decoration: none;
        }
        .nav-brand .logo {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 1.1rem;
            color: var(--bg-primary);
        }
        .nav-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(0,255,136,0.1);
            border: 1px solid rgba(0,255,136,0.2);
            color: var(--accent-green);
            font-size: 0.85rem;
            font-weight: 500;
        }
        .nav-status .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            animation: blink 2s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .chat-container {
            flex: 1;
            max-width: 1200px;
            margin: 80px auto 0;
            width: 100%;
            padding: 0 24px;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 80px);
        }
        .chat-window {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }
        .chat-header {
            background: var(--bg-secondary);
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-title {
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .chat-status {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            display: flex;
            gap: 12px;
            max-width: 80%;
        }
        .message.user {
            flex-direction: row-reverse;
            margin-left: auto;
        }
        .message.avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }
        .message.delta {
            background: linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.1));
            border: 1px solid rgba(0,255,136,0.3);
        }
        .message.user {
            background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(168,85,247,0.1));
            border: 1px solid rgba(0,212,255,0.3);
        }
        .message-content {
            padding: 12px 16px;
            border-radius: var(--radius);
            word-wrap: break-word;
        }
        .message.delta .message-content {
            background: var(--bg-card);
            border: 1px solid rgba(0,255,136,0.3);
        }
        .message.user .message-content {
            background: var(--bg-card);
            border: 1px solid rgba(0,212,255,0.3);
        }
        .message-time {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 4px;
            display: block;
        }
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-radius: var(--radius);
            margin-left: 44px;
            margin-bottom: 8px;
            color: var(--accent-green);
            font-style: italic;
            border: 1px solid rgba(0,255,136,0.3);
            animation: pulseGlow 1.5s ease-in-out infinite;
        }
        .typing-indicator.show {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        @keyframes pulseGlow {
            0%, 100% { box-shadow: 0 0 4px rgba(0,255,136,0.2); }
            50% { box-shadow: 0 0 12px rgba(0,255,136,0.5); }
        }
        .dot-bounce {
            width: 6px;
            height: 6px;
            background-color: var(--accent-green);
            border-radius: 50%;
            display: inline-block;
            animation: dotBounce 1.4s infinite ease-in-out both;
        }
        .dot-bounce:nth-child(1) { animation-delay: -0.32s; }
        .dot-bounce:nth-child(2) { animation-delay: -0.16s; }
        .dot-bounce:nth-child(3) { animation-delay: 0s; }
        @keyframes dotBounce {
            0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
            40% { transform: scale(1); opacity: 1; }
        }
        .input-container {
            padding: 20px 24px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
        }
        .input-wrapper {
            display: flex;
            gap: 12px;
            max-width: 800px;
            margin: 0 auto;
        }
        .message-input {
            flex: 1;
            background: var(--bg-primary);
            border: 1px solid var(--border-active);
            border-radius: var(--radius-lg);
            padding: 12px 16px;
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 0.95rem;
            resize: none;
            min-height: 44px;
            max-height: 120px;
            transition: var(--transition);
        }
        .message-input:focus {
            outline: none;
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
        }
        .send-button {
            background: linear-gradient(135deg, var(--accent-green), #00cc6a);
            border: none;
            border-radius: var(--radius-lg);
            padding: 12px 24px;
            color: var(--bg-primary);
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .send-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,255,136,0.3);
        }
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .quick-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .quick-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-active);
            border-radius: var(--radius);
            padding: 6px 12px;
            color: var(--text-secondary);
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
        }
        .quick-btn:hover {
            border-color: var(--accent-green);
            color: var(--accent-green);
            background: rgba(0,255,136,0.05);
        }
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-radius: var(--radius);
            margin-left: 44px;
            margin-bottom: 8px;
            color: var(--accent-green);
            font-style: italic;
            align-self: flex-start;
        }
        .typing-indicator.show {
            display: block;
        }
        @media (max-width: 768px) {
            .message {
                max-width: 90%;
            }
            .chat-container {
                margin-top: 70px;
            }
            .input-wrapper {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <nav class="nav">
        <a href="http://localhost:8080" class="nav-brand">
            <div class="logo">Δ</div>
            Delta AI Security Chat
        </a>
        <div class="nav-status">
            <span class="dot"></span>
            <span>AI LLM Mode: ACTIVE</span>
        </div>
    </nav>

    <div class="chat-container">
        <div class="chat-window">
            <div class="chat-header">
                <div class="chat-title">
                    <span>💅 Delta AI - Your Security Assistant</span>
                </div>
                <div class="chat-status">
                    {status_info}
                </div>
            </div>

            <div class="messages-container" id="messagesContainer">
                {messages_html}
            </div>

            <div class="typing-indicator" id="typingIndicator">
                <span>💅 Delta AI sedang berpikir...</span>
                <span class="dot-bounce"></span>
                <span class="dot-bounce"></span>
                <span class="dot-bounce"></span>
            </div>

            <div class="input-container">
                <div class="input-wrapper">
                    <textarea
                        class="message-input"
                        id="messageInput"
                        placeholder="Type your security question or command..."
                        onkeydown="handleKeyPress(event)"
                    ></textarea>
                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        <span>Send</span>
                        <span>→</span>
                    </button>
                </div>
                <div class="quick-actions">
                    <button class="quick-btn" onclick="quickCommand('scan localhost')">🔍 Scan localhost</button>
                    <button class="quick-btn" onclick="quickCommand('check security on localhost')">🛡️ Check security</button>
                    <button class="quick-btn" onclick="quickCommand('audit localhost')">📊 Audit system</button>
                    <button class="quick-btn" onclick="quickCommand('help')">❓ Help</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = '{session_id}';
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function formatTime(date) {
            return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function createMessageElement(message, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'delta'}`;

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = isUser ? 'T' : 'Δ';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';

            if (isUser) {
                contentDiv.textContent = message;
            } else {
                contentDiv.innerHTML = formatDeltaMessage(message);
            }

            const timeDiv = document.createElement('span');
            timeDiv.className = 'message-time';
            timeDiv.textContent = formatTime(new Date());

            contentDiv.appendChild(timeDiv);
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);

            return messageDiv;
        }

        function formatDeltaMessage(text) {
            // Convert markdown to HTML with Delta's personality styling
            let html = escapeHtml(text);

            // Style specific elements
            html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--accent-green); font-weight: 600;">\$1</strong>');
            html = html.replace(/\*(.*?)\*/g, '<em style="color: var(--accent-cyan);">\$1</em>');
            html = html.replace(/`(.*?)`/g, '<code style="background: rgba(0,212,255,0.1); color: var(--accent-cyan); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">$1</code>');
            html = html.replace(/\n/g, '<br>');

            // Add Delta's signature style to important parts
            html = html.replace(/Delta AI/g, '<span style="color: var(--accent-purple); font-weight: 600;">Delta AI</span>');

            return html;
        }

        function addMessage(message, isUser = false) {
            const container = document.getElementById('messagesContainer');
            const messageEl = createMessageElement(message, isUser);
            container.appendChild(messageEl);
            container.scrollTop = container.scrollHeight;
        }

        function showTypingIndicator(show) {
            const indicator = document.getElementById('typingIndicator');
            if (show) {
                indicator.classList.add('show');
            } else {
                indicator.classList.remove('show');
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const button = document.getElementById('sendButton');
            const message = input.value.trim();

            if (!message) return;

            input.value = '';
            input.disabled = true;
            button.disabled = true;

            // Add user message
            addMessage(message, true);

            // Show typing indicator
            showTypingIndicator(true);

            try {
                // Send to Delta backend
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: currentSessionId
                    })
                });

                const data = await response.json();

                showTypingIndicator(false);

                if (data.response) {
                    addMessage(data.response, false);
                }

            } catch (error) {
                showTypingIndicator(false);
                addMessage('Ada kendala koneksi nih. Coba lagi bentar ya.', false);
                console.error('Chat error:', error);
            } finally {
                input.disabled = false;
                button.disabled = false;
                input.focus();
            }
        }

        function quickCommand(command) {
            document.getElementById('messageInput').value = command;
            sendMessage();
        }

        function connectWebSocket() {
            ws = new WebSocket(`ws://localhost:8000/ws/chat/${currentSessionId}`);

            ws.onopen = function(event) {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'delta_message') {
                    addMessage(data.message, false);
                    showTypingIndicator(false);
                }
            };

            ws.onclose = function(event) {
                console.log('WebSocket disconnected');
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(connectWebSocket, 1000 * (reconnectAttempts + 1));
                    reconnectAttempts++;
                }
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                showTypingIndicator(false);
            };
        }

        function init() {
            connectWebSocket();

            // Add welcome message
            setTimeout(() => {
                addMessage('Hai! Aku Delta. Mau ngerjain project atau ada bug apa yang mau dibenerin?', false);
                setTimeout(() => {
                    addMessage('Coba ketik `scan localhost` atau langsung ngobrol santai ya.', false);
                }, 1000);
            }, 500);
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""


class DeltaChatInterface:
    def __init__(self, config_path: Optional[str] = None):
        self.app = Flask(__name__)
        self.config = DeltaConfig()
        self.config.load(config_path)

        self.display = DisplayManager()
        self.session_id = f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.setup_routes()

        # Initialize Delta engine
        self.engine = self._create_delta_engine()

    def _create_delta_engine(self) -> DeltaEngine:
        """Create and initialize Delta engine."""
        from delta.core.config import DeltaConfig
        from delta.core.engine import DeltaEngine
        from delta.core.database import Database
        from delta.core.session import SessionManager
        from delta.ai.intent import IntentEngine
        from delta.ai.llm import LLMEngine
        from delta.ai.memory import MemoryManager
        from delta.core.plugin import PluginManager
        from delta.core.display import DisplayManager

        config = DeltaConfig()
        config.load()

        display = DisplayManager()

        import os
        db_path = os.path.join(config.data_dir, "delta.db")
        database = Database(db_path)
        database.initialize()

        session = SessionManager(database)

        intent_engine = IntentEngine(config, database)

        plugin_manager = PluginManager(config.plugin_dir)

        memory_dir = os.path.join(config.data_dir, "memory")
        memory_manager = MemoryManager(memory_dir, max_sessions=config.max_sessions)

        llm_engine = LLMEngine(
            api_key=config.llm_api_key,
            base_url=config.llm_api_base_url or None,
            model=config.llm_model or None,
            provider=config.llm_provider or None,
            memory_manager=memory_manager,
            memory_enabled=config.memory_enabled,
            max_retries=config.llm_max_retries,
            retry_backoff_factor=config.llm_retry_backoff_factor,
            retry_initial_delay=config.llm_retry_initial_delay,
            retry_max_delay=config.llm_retry_max_delay,
        )

        engine = DeltaEngine(
            config=config,
            database=database,
            session=session,
            intent_engine=intent_engine,
            plugin_manager=plugin_manager,
            display=display,
            llm_engine=llm_engine,
        )

        return engine

    def setup_routes(self):
        @self.app.route('/')
        def chat_page():
            status_info = "Ready to assist you!"
            if self.engine and self.engine.llm_engine and self.engine.llm_engine.is_configured:
                status_info = f"AI LLM Mode: ACTIVE - {self.engine.llm_engine.provider} - {self.engine.llm_engine.model}"

            template = CHAT_TEMPLATE
            template = template.replace('{status_info}', status_info)
            template = template.replace('{session_id}', self.session_id)
            template = template.replace('{messages_html}', '')

            return template

        @self.app.route('/api/chat', methods=['POST'])
        def chat_api():
            try:
                data = request.get_json()
                user_message = data.get('message', '')
                session_id = data.get('session_id', self.session_id)

                if not user_message:
                    return jsonify({'error': 'Message required'}), 400

                # Process message through Delta engine
                response = self._process_message(user_message, session_id)

                return jsonify({
                    'response': response,
                    'session_id': session_id
                })

            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'response': 'Ada kendala teknis sebentar nih. Coba lagi ya.'
                }), 500

        @self.app.route('/api/status')
        def status_api():
            cwd = getattr(self.engine, "cwd", None) or os.getcwd() if self.engine else os.getcwd()
            status = {
                'engine_running': True,
                'working_directory': cwd,
                'llm_configured': self.engine.llm_engine.is_configured if self.engine else False,
                'provider': self.engine.llm_engine.provider if self.engine and self.engine.llm_engine else 'none',
                'model': self.engine.llm_engine.model if self.engine and self.engine.llm_engine else 'none'
            }
            return jsonify(status)

    def _process_message(self, message: str, session_id: str) -> str:
        """Process message through Delta engine."""
        try:
            # Add to conversation
            self.engine.session.add_conversation("user", message)

            # Process with LLM if available
            if self.engine.llm_engine and self.engine.llm_engine.is_configured and self.engine.config.llm_enabled:
                response = self.engine.llm_engine.chat(message)

                # Parse response for command
                from delta.ai.llm import parse_command_from_response, strip_command_tags
                command = parse_command_from_response(response)
                clean_response = strip_command_tags(response)

                if command:
                    # Execute command
                    self.engine._dispatch_command(command)

                    # Get last result for display
                    if self.engine.last_result:
                        clean_response += f"\n\n**Result:** {self.engine.last_result}"

                return clean_response

            # Process with intent engine
            intent = self.engine.intent_engine.process(message, self.engine.session.context)
            if intent:
                self.engine._execute_with_ai(intent, message)
                return f"I've analyzed your request and executed: {intent.intent.value}"

            # Direct command dispatch
            self.engine._dispatch_command(message)
            return f"Command executed: {message}"

        except Exception as e:
            return f"Ada kendala saat proses pesan: {str(e)}"

    def run(self, host='0.0.0.0', port=8000):
        """Run the web chat server."""
        print(f"🚀 Delta Web Chat starting on http://{host}:{port}")
        print(f"📱 Chat session ID: {self.session_id}")
        print("💅 Delta AI Security Chat is ready to assist you!")

        self.app.run(host=host, port=port, debug=False)