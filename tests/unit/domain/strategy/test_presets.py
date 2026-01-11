from unittest.mock import MagicMock
from datetime import date
from src.domain.strategy.presets.always_buy_evaluator import AlwaysBuyEvaluator
from src.domain.strategy.presets.buy_and_hold_strategy import BuyAndHoldStrategy
from src.domain.strategy.trading_signal import SignalType

def test_always_buy_evaluator():
    evaluator = AlwaysBuyEvaluator()
    mock_chart = MagicMock()
    
    signal = evaluator.evaluate(mock_chart, 0)
    
    assert signal.type == SignalType.BUY
    assert signal.quantity is None
    assert "Always Buy" in signal.reason

def test_buy_and_hold_strategy():
    strategy = BuyAndHoldStrategy()
    
    # Mock Universe
    mock_chart = MagicMock()
    mock_chart.find_index_by_date.return_value = 5 # 데이터 있음
    mock_chart.ticker.code = "TEST" # Mock Ticker
    
    universe = {"TEST": mock_chart}
    current_date = date(2025, 1, 1)
    
    results = strategy.analyze(universe, current_date)
    
    assert len(results) == 1
    assert "TEST" in results
    assert results["TEST"].type == SignalType.BUY
    assert results["TEST"].quantity is None
