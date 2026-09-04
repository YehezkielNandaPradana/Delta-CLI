"""Camera Monitoring Session & WebRTC Signaling Manager for Delta."""

import time
import uuid
from typing import Any, Dict, List, Optional


class CameraSignalingManager:
    """Manages active WebRTC monitoring sessions, SDP offers/answers, and ICE candidates."""

    def __init__(self, session_ttl_sec: float = 3600.0):
        self.session_ttl_sec = session_ttl_sec
        # sessions: { sessionId: { metadata, created_at, expires_at, status, queues... } }
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def init_session(
        self, device_id: str, platform: str = "android", facing: str = "back"
    ) -> Dict[str, Any]:
        """Create a new camera monitoring session."""
        now = time.time()
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        auth_token = f"tok_{uuid.uuid4().hex[:16]}"

        session_data = {
            "sessionId": session_id,
            "token": auth_token,
            "deviceId": device_id,
            "platform": platform,
            "facing": facing,
            "status": "CONNECTING",
            "created_at": now,
            "expires_at": now + self.session_ttl_sec,
            # Signals queue for sender (mobile) and viewer (web)
            "sender_signals": [],
            "viewer_signals": [],
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"},
            ],
        }

        self._sessions[session_id] = session_data
        return {
            "status": "ok",
            "sessionId": session_id,
            "token": auth_token,
            "expiresAt": session_data["expires_at"],
            "iceServers": session_data["ice_servers"],
        }

    def post_signal(
        self, session_id: str, role: str, signal_type: str, data: Any
    ) -> Dict[str, Any]:
        """Route SDP/ICE signals between mobile sender and web viewer."""
        session = self._sessions.get(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        if time.time() > session["expires_at"] or session["status"] == "STOPPED":
            return {"status": "error", "message": "Session expired or stopped"}

        msg = {"type": signal_type, "data": data, "timestamp": time.time()}

        if role == "sender":
            # Signal from sender goes to viewer queue
            session["viewer_signals"].append(msg)
            if signal_type == "offer":
                session["status"] = "MONITORING"
        else:
            # Signal from viewer goes to sender queue
            session["sender_signals"].append(msg)

        return {"status": "ok"}

    def poll_signals(self, session_id: str, role: str) -> List[Dict[str, Any]]:
        """Retrieve and drain pending signals for role (sender or viewer)."""
        session = self._sessions.get(session_id)
        if not session:
            return []

        if time.time() > session["expires_at"] or session["status"] == "STOPPED":
            return [{"type": "stop", "data": "Session closed"}]

        if role == "sender":
            signals = session["sender_signals"]
            session["sender_signals"] = []
            return signals
        else:
            signals = session["viewer_signals"]
            session["viewer_signals"] = []
            return signals

    def stop_session(self, session_id: str) -> Dict[str, Any]:
        """Revoke monitoring session and stop stream."""
        session = self._sessions.get(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        session["status"] = "STOPPED"
        stop_msg = {"type": "stop", "data": "User revoked session", "timestamp": time.time()}
        session["sender_signals"].append(stop_msg)
        session["viewer_signals"].append(stop_msg)
        return {"status": "ok", "message": f"Session {session_id} stopped"}

    def get_session_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get active session details or general camera system status."""
        now = time.time()
        if session_id and session_id in self._sessions:
            s = self._sessions[session_id]
            is_valid = s["status"] in ("CONNECTING", "MONITORING") and s["expires_at"] > now
            return {
                "is_live": is_valid,
                "status": s["status"] if is_valid else "OFFLINE",
                "sessionId": s["sessionId"],
                "device": s["deviceId"],
                "platform": s["platform"],
                "facing": s["facing"],
                "uptime_sec": round(now - s["created_at"], 1) if is_valid else 0,
                "ice_servers": s["ice_servers"],
            }

        # Find latest active non-expired session
        active_sessions = [
            s
            for s in self._sessions.values()
            if s["status"] in ("CONNECTING", "MONITORING") and s["expires_at"] > now
        ]

        if not active_sessions:
            return {
                "is_live": False,
                "status": "OFFLINE",
                "device": None,
                "active_sessions_count": 0,
            }

        latest = active_sessions[-1]
        return {
            "is_live": True,
            "status": latest["status"],
            "sessionId": latest["sessionId"],
            "device": latest["deviceId"],
            "platform": latest["platform"],
            "facing": latest["facing"],
            "uptime_sec": round(now - latest["created_at"], 1),
            "ice_servers": latest["ice_servers"],
            "active_sessions_count": len(active_sessions),
        }


# Singleton instance for Delta Web backend
camera_signaling = CameraSignalingManager()
