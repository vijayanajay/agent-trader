from src.risk_manager import compute_risk


# --- Tests for Risk Manager ---

def test_compute_risk_happy_path() -> None:
    """Tests standard risk calculation."""
    params = compute_risk(current_price=100.0, current_atr=5.0)
    assert params["stop_loss"] == 90.0
    assert params["take_profit"] == 120.0

def test_compute_risk_zero_atr() -> None:
    """Tests edge case where ATR is zero."""
    params = compute_risk(current_price=100.0, current_atr=0.0)
    assert params["stop_loss"] == 100.0
    assert params["take_profit"] == 100.0
