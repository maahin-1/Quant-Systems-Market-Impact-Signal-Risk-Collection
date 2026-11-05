def interpret_market_impact(symbol: str, metric: str, mean: float, slope: float) -> str:
    return (
        f"You are a quant analyst specializing in Indian markets.\n"
        f"Symbol: {symbol} | Metric: {metric}\n"
        f"Curve stats: mean={mean:.4f}, slope={slope:.4f}\n"
        f"Interpret what this market impact curve shape tells us about liquidity "
        f"and market conditions. Be specific and concise. 3-5 sentences."
    )


def signal_decay_prompt(symbol: str, half_life: float, current_bar: int) -> str:
    return (
        f"You are a quant analyst specializing in Indian markets.\n"
        f"Symbol: {symbol}\n"
        f"Signal half-life: {half_life} bars. Current position: bar {current_bar}.\n"
        f"Is this signal still actionable or has it decayed past threshold? "
        f"Recommend: hold, exit, or monitor. 3-5 sentences."
    )


def anomaly_alert_prompt(
    symbol: str, metric: str, current: float, mean: float, sigma: float
) -> str:
    z = (current - mean) / sigma if sigma != 0 else 0.0
    return (
        f"You are a quant analyst specializing in Indian markets.\n"
        f"Anomaly detected for {symbol} | Metric: {metric}\n"
        f"Current: {current:.4f}, 20-day mean: {mean:.4f}, Std: {sigma:.4f}, "
        f"Z-score: {z:.2f}\n"
        f"Identify probable causes and suggest a specific action. 3-5 sentences."
    )
