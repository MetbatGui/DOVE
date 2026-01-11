from typing import Optional
from decimal import Decimal
from src.domain.strategy.asset_evaluator import AssetEvaluator
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.trading_signal import TradingSignal, SignalType

class AlwaysBuyEvaluator(AssetEvaluator):
    """
    무조건 매수 신호를 생성하는 평가기.
    """
    def evaluate(self, chart: CandleChart, current_index: int) -> TradingSignal:
        """
        항상 BUY 신호를 반환합니다.
        수량(quantity)을 None으로 설정하여 가능한 최대 수량을 매수하도록 합니다.
        """
        return TradingSignal(
            type=SignalType.BUY,
            quantity=None,
            reason="Always Buy Evaluator Triggered"
        )
