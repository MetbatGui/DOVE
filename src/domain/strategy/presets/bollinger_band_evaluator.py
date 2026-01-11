from typing import Dict
from src.domain.strategy.asset_evaluator import AssetEvaluator
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.trading_signal import TradingSignal, SignalType
from src.domain.technical.bollinger_bands import BollingerBands
from src.domain.shared.money import Money

class BollingerBandEvaluator(AssetEvaluator):
    """
    볼린저 밴드 기반의 평균 회귀(Mean Reversion) 평가기.
    - 하락하여 하단 밴드 이하로 떨어지면 과매도로 판단하여 매수(BUY).
    - 상승하여 상단 밴드 이상으로 올라가면 과매수로 판단하여 매도(SELL).
    """
    
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        self.bb = BollingerBands(period=period, std_dev_multiplier=multiplier)

    def evaluate(self, chart: CandleChart, current_index: int) -> TradingSignal:
        if current_index < self.bb.period - 1:
            return TradingSignal(type=SignalType.HOLD)
            
        # 전체 차트에 대해 볼린저 밴드 계산 (매번 계산은 비효율적일 수 있으나 일단 명확성을 위해 구현)
        # 최적화: 캐싱하거나 필요한 부분만 계산하도록 개선 가능
        upper_band, _, lower_band = self.bb.calculate(chart)
        
        # 현재 시점의 데이터 확인
        current_candle = chart.candles[current_index]
        current_price = current_candle.close_price
        
        current_upper = upper_band[current_index]
        current_lower = lower_band[current_index]
        
        if current_upper is None or current_lower is None:
             return TradingSignal(type=SignalType.HOLD)

        # 매수 조건: 종가 <= 하단 밴드
        if current_price.amount <= current_lower.amount:
            return TradingSignal(
                type=SignalType.BUY,
                quantity=None, # 자금에 맞춰 최대 매수
                reason=f"Close({current_price.amount}) <= LowerBand({current_lower.amount:.2f})"
            )
            
        # 매도 조건: 종가 >= 상단 밴드
        elif current_price.amount >= current_upper.amount:
            return TradingSignal(
                type=SignalType.SELL,
                quantity=None, # 전량 매도
                reason=f"Close({current_price.amount}) >= UpperBand({current_upper.amount:.2f})"
            )
            
        return TradingSignal(type=SignalType.HOLD)
