from typing import List, Optional
from pydantic import BaseModel, field_validator
from decimal import Decimal
from src.domain.technical.indicator import Indicator
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money

class MovingAverage(BaseModel, Indicator):
    """
    단순 이동평균(Simple Moving Average)을 계산하는 지표입니다.
    종가(Close Price)를 기준으로 계산합니다.
    """
    period: int

    @field_validator('period')
    @classmethod
    def validate_period(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Period must be positive")
        return v

    def calculate(self, chart: CandleChart) -> List[Optional[Money]]:
        """
        이동평균을 계산하여 리스트로 반환합니다.
        데이터가 충분하지 않은 앞부분(period - 1개)은 None으로 채워집니다.
        
        Returns:
            List[Optional[Money]]: 이동평균 값들의 리스트. 
                                 인덱스는 캔들 차트의 인덱스와 1:1로 대응됩니다.
        """
        candles = chart.candles
        if len(candles) < self.period:
            return [None] * len(candles)

        results: List[Optional[Money]] = [None] * (self.period - 1)
        
        # 첫 번째 윈도우 합계 계산
        current_sum = Decimal(0)
        for i in range(self.period):
            current_sum += candles[i].close_price.amount
            
        # 첫 번째 평균 추가
        currency = candles[0].close_price.currency
        results.append(Money(amount=current_sum / self.period, currency=currency))

        # 슬라이딩 윈도우로 나머지 계산
        for i in range(self.period, len(candles)):
            # 윈도우에서 빠지는 값(가장 오래된 값) 빼고, 들어오는 값(현재 값) 더하기
            remove_idx = i - self.period
            current_sum -= candles[remove_idx].close_price.amount
            current_sum += candles[i].close_price.amount
            
            results.append(Money(amount=current_sum / self.period, currency=currency))

        return results
