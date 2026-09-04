"""End-to-End integration test for Camera Monitoring permission & WebRTC signaling flow."""

from delta.web.camera_signaling import CameraSignalingManager


def test_camera_monitoring_e2e_flow():
    signaling = CameraSignalingManager(session_ttl_sec=30.0)

    # 1. Device requests to initialize monitoring session
    init_res = signaling.init_session(
        device_id="Android-Sec-Terminal-01",
        platform="android",
        facing="back"
    )
    assert init_res["status"] == "ok"
    session_id = init_res["sessionId"]
    token = init_res["token"]
    assert session_id is not None
    assert token is not None

    # 2. Verify device status is actively monitored
    status = signaling.get_session_status()
    assert status["is_live"] is True
    assert status["sessionId"] == session_id
    assert status["device"] == "Android-Sec-Terminal-01"

    # 3. Mobile sender sends SDP offer
    sdp_offer = {"type": "offer", "sdp": "m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"}
    post_offer_res = signaling.post_signal(
        session_id=session_id,
        role="sender",
        signal_type="offer",
        data=sdp_offer
    )
    assert post_offer_res["status"] == "ok"

    # 4. Web viewer polls and receives SDP offer
    viewer_signals = signaling.poll_signals(session_id=session_id, role="viewer")
    assert len(viewer_signals) == 1
    assert viewer_signals[0]["type"] == "offer"

    # 5. Web viewer responds with SDP answer
    sdp_answer = {"type": "answer", "sdp": "m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"}
    post_answer_res = signaling.post_signal(
        session_id=session_id,
        role="viewer",
        signal_type="answer",
        data=sdp_answer
    )
    assert post_answer_res["status"] == "ok"

    # 6. Mobile sender polls and receives SDP answer
    sender_signals = signaling.poll_signals(session_id=session_id, role="sender")
    assert len(sender_signals) == 1
    assert sender_signals[0]["type"] == "answer"

    # 7. Candidate exchange
    cand = {"candidate": "candidate:1 1 UDP 2130706431 192.168.1.50 50000 typ host"}
    signaling.post_signal(session_id, role="sender", signal_type="candidate", data=cand)
    cand_signals = signaling.poll_signals(session_id, role="viewer")
    assert len(cand_signals) == 1
    assert cand_signals[0]["type"] == "candidate"

    # 8. Stop Monitoring Session
    stop_res = signaling.stop_session(session_id)
    assert stop_res["status"] == "ok"

    # 9. Verify teardown
    final_status = signaling.get_session_status()
    assert final_status["is_live"] is False
    assert final_status["status"] == "OFFLINE"

    # Poll on stopped session returns stop signal
    signals_after_stop = signaling.poll_signals(session_id, role="sender")
    assert any(s["type"] == "stop" for s in signals_after_stop)

    print("PASS: test_camera_monitoring_e2e_flow succeeded.")


if __name__ == "__main__":
    test_camera_monitoring_e2e_flow()
