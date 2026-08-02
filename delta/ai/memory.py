import json

import os

from typing import Dict, List, Optional, Any

from datetime import datetime

class MemoryManager:

    def __init__(self, memory_dir: str, max_sessions: int = 50):

        self.memory_dir = memory_dir

        self.max_sessions = max_sessions

        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    def save_conversation(self, session_id: str, messages: List[Dict[str, str]]) -> None:

        os.makedirs(self.memory_dir, exist_ok=True)

        path = self._session_path(session_id)

        system_msgs = [m for m in messages if m["role"] == "system"]

        non_system = [m for m in messages if m["role"] != "system"]

        data = {

            "session_id": session_id,

            "updated_at": datetime.now().isoformat(),

            "system_messages": system_msgs,

            "conversation": non_system,

            "total_messages": len(messages),

        }

        with open(path, "w") as f:

            json.dump(data, f, indent=2)

        self._trim_sessions()

    def load_conversation(self, session_id: str) -> List[Dict[str, str]]:

        path = self._session_path(session_id)

        if not os.path.exists(path):

            return []

        try:

            with open(path, "r") as f:

                data = json.load(f)

            return data.get("system_messages", []) + data.get("conversation", [])

        except (json.JSONDecodeError, IOError):

            return []

    def list_sessions(self) -> List[Dict[str, Any]]:

        if not os.path.exists(self.memory_dir):

            return []

        sessions = []

        for fname in os.listdir(self.memory_dir):

            if fname.endswith(".json"):

                path = os.path.join(self.memory_dir, fname)

                try:

                    with open(path, "r") as f:

                        data = json.load(f)

                    sessions.append({

                        "session_id": data.get("session_id", fname.replace(".json", "")),

                        "updated_at": data.get("updated_at", "unknown"),

                        "messages": data.get("total_messages", 0),

                    })

                except (json.JSONDecodeError, IOError):

                    continue

        return sorted(sessions, key=lambda s: s.get("updated_at", ""), reverse=True)

    def delete_session(self, session_id: str) -> bool:

        path = self._session_path(session_id)

        if os.path.exists(path):

            os.remove(path)

            self._sessions.pop(session_id, None)

            return True

        return False

    def clear_all(self) -> int:

        count = 0

        if os.path.exists(self.memory_dir):

            for fname in os.listdir(self.memory_dir):

                if fname.endswith(".json"):

                    os.remove(os.path.join(self.memory_dir, fname))

                    count += 1

        self._sessions.clear()

        return count

    def _session_path(self, session_id: str) -> str:

        safe = session_id.replace("/", "_").replace("\\", "_").replace(":", "_")

        return os.path.join(self.memory_dir, f"{safe}.json")

    def _trim_sessions(self) -> None:

        if not os.path.exists(self.memory_dir):

            return

        sessions = []

        for fname in os.listdir(self.memory_dir):

            if fname.endswith(".json"):

                path = os.path.join(self.memory_dir, fname)

                try:

                    mtime = os.path.getmtime(path)

                    sessions.append((path, mtime))

                except OSError:

                    continue

        sessions.sort(key=lambda x: x[1], reverse=True)

        if len(sessions) > self.max_sessions:

            for path, _ in sessions[self.max_sessions:]:

                try:

                    os.remove(path)

                except OSError:

                    pass