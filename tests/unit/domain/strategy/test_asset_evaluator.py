import pytest
from unittest.mock import MagicMock
from src.domain.strategy.asset_evaluator import AssetEvaluator
from src.domain.strategy.trading_signal import TradingSignal, SignalType

class TestableAssetEvaluator(AssetEvaluator):
    """테스트를 위한 AssetEvaluator 구현체"""
    def evaluate(self, chart, current_index: int) -> TradingSignal:
        latest_close = chart.get_close_price(current_index)
        
        if latest_close > 100:
            return TradingSignal(type=SignalType.BUY, reason="Price > 100")
        else:
            return TradingSignal(type=SignalType.SELL, reason="Price <= 100")

def test_asset_evaluator_buy_signal():
    """외부 의존성(CandleChart, Ticker 등) 없이 Mock을 사용하여 테스트"""
    # Arrange
    evaluator = TestableAssetEvaluator()
    
    # Mocking CandleChart
    # 실제 CandleChart 클래스를 import하지 않고, 필요한 동작만 하는 가짜 객체 생성
    mock_chart = MagicMock()
    # evaluate 메서드 내부에서 호출하는 get_close_price가 150을 반환하도록 설정
    mock_chart.get_close_price.return_value = 150
    
    # Act
    signal = evaluator.evaluate(mock_chart, 0)
    
    # Assert
    assert signal.type == SignalType.BUY
    assert signal.reason == "Price > 100"
    
    # Mock 객체가 올바르게 사용되었는지 검증
    mock_chart.get_close_price.assert_called_once_with(0)

def test_asset_evaluator_sell_signal():
    """외부 의존성 없이 Sell 시그널 테스트"""
    # Arrange
    evaluator = TestableAssetEvaluator()
    
    # Mocking CandleChart
    mock_chart = MagicMock()
    mock_chart.get_close_price.return_value = 50
    
    # Act
    signal = evaluator.evaluate(mock_chart, 0)
    
    # Assert
    assert signal.type == SignalType.SELL
    assert signal.reason == "Price <= 100"
