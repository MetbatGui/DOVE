from unittest.mock import MagicMock, patch
from decimal import Decimal
from src.domain.strategy.presets.bollinger_band_evaluator import BollingerBandEvaluator
from src.domain.strategy.trading_signal import SignalType
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit

class TestBollingerBandEvaluator:
    @patch('src.domain.strategy.presets.bollinger_band_evaluator.BollingerBands')
    def test_evaluate_signals(self, MockBollingerBands):
        # Mock Bollinger Bands instance
        mock_bb_instance = MockBollingerBands.return_value
        mock_bb_instance.period = 20
        
        # Mock calculate return values (Upper, Middle, Lower)
        # 23일치 데이터 가정 (0~19: None, 20=Hold, 21=Buy, 22=Sell)
        
        # 앞부분 20개는 데이터 부족으로 None처리 or 의미없는 값
        dummy_list = [None] * 20
        
        mock_upper = dummy_list + [
            MagicMock(amount=Decimal("110")),  # Index 20
            MagicMock(amount=Decimal("110")),  # Index 21
            MagicMock(amount=Decimal("100"))   # Index 22
        ]
        mock_lower = dummy_list + [
            MagicMock(amount=Decimal("90")),   # Index 20
            MagicMock(amount=Decimal("100")),  # Index 21
            MagicMock(amount=Decimal("90"))    # Index 22
        ]
        mock_middle = [None] * 23
        
        mock_bb_instance.calculate.return_value = (mock_upper, mock_middle, mock_lower)
        
        # Create Evaluator
        evaluator = BollingerBandEvaluator()
        
        # Mock Chart
        mock_chart = MagicMock()
        
        # Index 접근을 위해 리스트 길이 맞춰줌
        candles = [MagicMock()] * 20 + [
            MagicMock(close_price=MagicMock(amount=Decimal("100"))), # Index 20: 100 (90 < 100 < 110) -> HOLD
            MagicMock(close_price=MagicMock(amount=Decimal("95"))),  # Index 21: 95 <= 100 (Lower) -> BUY
            MagicMock(close_price=MagicMock(amount=Decimal("105"))), # Index 22: 105 >= 100 (Upper) -> SELL
        ]
        mock_chart.candles = candles
        
        # Test Index 20 (HOLD)
        signal0 = evaluator.evaluate(mock_chart, 20)
        assert signal0.type == SignalType.HOLD
        
        # Test Index 21 (BUY) -- Logic Check: Price(95) <= Lower(100)
        signal1 = evaluator.evaluate(mock_chart, 21)
        assert signal1.type == SignalType.BUY
        assert "LowerBand" in signal1.reason
        
        # Test Index 22 (SELL) -- Logic Check: Price(105) >= Upper(100)
        signal2 = evaluator.evaluate(mock_chart, 22)
        assert signal2.type == SignalType.SELL
        assert "UpperBand" in signal2.reason
