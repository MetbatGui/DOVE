from typing import List, Optional
from pydantic import BaseModel, field_validator
from decimal import Decimal
from src.domain.technical.indicator import Indicator
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money

class EMA(BaseModel, Indicator):
    """
    EMA (Exponential Moving Average) 지수 이동평균 지표
    """
    period: int = 12

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Period must be at least 1")
        return v

    def calculate(self, chart: CandleChart) -> List[Optional[Money]]:
        candles = chart.candles
        if len(candles) < self.period:
            return [None] * len(candles)

        results: List[Optional[Money]] = [None] * (self.period - 1)
        
        # 1. 초기값: 첫 period의 SMA로 시작하는 것이 일반적 관례
        # (TradingView 등 많은 플랫폼이 이 방식을 따름)
        initial_sum = sum((c.close_price.amount for c in candles[:self.period]), Decimal(0))
        initial_sma = initial_sum / self.period
        
        currency = candles[0].close_price.currency
        results.append(Money(amount=initial_sma, currency=currency))

        # 2. EMA 계산
        # Multiplier: k = 2 / (N + 1)
        k = Decimal(2) / (self.period + 1)

        prev_ema = initial_sma
        
        for i in range(self.period, len(candles)):
            close = candles[i].close_price.amount
            # EMA = (Close - Prev_EMA) * k + Prev_EMA
            #     = Close * k + Prev_EMA * (1 - k)
            current_ema = (close * k) + (prev_ema * (Decimal(1) - k))
            results.append(Money(amount=current_ema, currency=currency))
            prev_ema = current_ema

        return results
