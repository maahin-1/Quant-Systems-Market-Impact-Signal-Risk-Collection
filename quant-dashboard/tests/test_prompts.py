def test_interpret_market_impact_contains_symbol_and_metric():
    from llm.prompts import interpret_market_impact
    result = interpret_market_impact("RELIANCE.NS", "volatility", 0.05, 0.001)
    assert "RELIANCE.NS" in result
    assert "volatility" in result
    assert "0.0500" in result


def test_interpret_market_impact_contains_slope():
    from llm.prompts import interpret_market_impact
    result = interpret_market_impact("TCS.NS", "returns", 0.02, 0.003)
    assert "0.0030" in result


def test_signal_decay_prompt_contains_symbol_and_halflife():
    from llm.prompts import signal_decay_prompt
    result = signal_decay_prompt("TCS.NS", 12.5, 8)
    assert "TCS.NS" in result
    assert "12.5" in result
    assert "8" in result


def test_anomaly_alert_prompt_contains_zscore():
    from llm.prompts import anomaly_alert_prompt
    result = anomaly_alert_prompt("GC=F", "volatility", 0.08, 0.05, 0.01)
    assert "GC=F" in result
    assert "volatility" in result
    assert "3.00" in result  # z = (0.08-0.05)/0.01 = 3.0


def test_anomaly_alert_prompt_zero_sigma_no_crash():
    from llm.prompts import anomaly_alert_prompt
    result = anomaly_alert_prompt("SI=F", "returns", 0.01, 0.01, 0.0)
    assert isinstance(result, str)
