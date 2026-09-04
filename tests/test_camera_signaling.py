"""Unit tests for Delta WebRTC Camera Signaling & Session Manager."""

from delta.web.camera_signaling import CameraSignalingManager


def test_signaling_session_lifecycle():
    mgr = CameraSignalingManager(session_ttl_sec=10.0)

    # 1. Initial State
    status = mgr.get_session_status()
    assert not status["is_live"]
    assert status["status"] == "OFFLINE"

    # 2. Init Session (Mobile Sender)
    res = mgr.init_session(device_id="Android-Device-Test", platform="android")
    assert res["status"] == "ok"
    session_id = res["sessionId"]
    assert session_id.startswith("sess_")
    assert "token" in res

    # 3. Check status is now live/connecting
    status = mgr.get_session_status()
    assert status["is_live"]
    assert status["device"] == "Android-Device-Test"

    # 4. Sender posts SDP Offer
    offer_payload = {"type": "offer", "sdp": "v=0\r\no=- 1234 2 IN IP4 127.0.0.1"}
    sig_res = mgr.post_signal(session_id, role="sender", signal_type="offer", data=offer_payload)
    assert sig_res["status"] == "ok"

    # 5. Viewer polls signals -> sees Offer
    viewer_signals = mgr.poll_signals(session_id, role="viewer")
    assert len(viewer_signals) == 1
    assert viewer_signals[0]["type"] == "offer"
    assert viewer_signals[0]["data"] == offer_payload

    # Queue must be drained
    assert len(mgr.poll_signals(session_id, role="viewer")) == 0

    # 6. Viewer posts SDP Answer
    answer_payload = {"type": "answer", "sdp": "v=0\r\no=- 5678 2 IN IP4 127.0.0.1"}
    mgr.post_signal(session_id, role="viewer", signal_type="answer", data=answer_payload)

    # Sender polls signals -> sees Answer
    sender_signals = mgr.poll_signals(session_id, role="sender")
    assert len(sender_signals) == 1
    assert sender_signals[0]["type"] == "answer"

    # 7. Stop Session
    stop_res = mgr.stop_session(session_id)
    assert stop_res["status"] == "ok"

    # Status must be offline now
    status_after = mgr.get_session_status()
    assert not status_after["is_live"]
    assert status_after["status"] == "OFFLINE"

    print("PASS: test_signaling_session_lifecycle succeeded.")


if __name__ == "__main__":
    test_signaling_session_lifecycle()
