from typing import Dict

__all__ = ["compute_risk"]


def compute_risk(current_price: float, current_atr: float) -> Dict[str, float]:
    """
    Calculates stop-loss and take-profit levels based on ATR.

    Args:
        current_price: The current price of the asset.
        current_atr: The current Average True Range of the asset.

    Returns:
        A dictionary with 'stop_loss' and 'take_profit' values.
    """
    if current_atr <= 0:
        # Cannot determine risk if volatility is zero or negative.
        # Return neutral values.
        return {"stop_loss": current_price, "take_profit": current_price}

    stop_loss = current_price - (2 * current_atr)
    take_profit = current_price + (4 * current_atr)

    return {"stop_loss": round(stop_loss, 2), "take_profit": round(take_profit, 2)}
