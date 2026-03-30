from app.services.mode_service import detect_mode


def test_detect_mode_returns_valid() -> None:
    assert detect_mode() in {"DEMO", "REAL"}
