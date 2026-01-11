from typing import List, Optional, Tuple
from decimal import Decimal
import math
from pydantic import BaseModel, field_validator
from src.domain.technical.indicator import Indicator
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.moving_average import MovingAverage

class BollingerBands(BaseModel, Indicator):
    """
    볼린저 밴드(Bollinger Bands) 지표
    - Middle Band: n일 이동평균선(SMA)
    - Upper Band: Middle Band + (k * 표준편차)
    - Lower Band: Middle Band - (k * 표준편차)
    """
    period: int = 20
    std_dev_multiplier: float = 2.0
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Period must be positive")
        return v

    def calculate(self, chart: CandleChart) -> Tuple[List[Optional[Money]], List[Optional[Money]], List[Optional[Money]]]:
        """
        볼린저 밴드를 계산합니다.
        
        Returns:
            (Upper Band, Middle Band, Lower Band)의 튜플 반환.
            각 리스트는 캔들 차트와 동일한 길이이며, 계산 불가능한 앞부분은 None.
        """
        candles = chart.candles
        if len(candles) < self.period:
            empty = [None] * len(candles)
            return empty, empty, empty
            
        # 1. Middle Band (SMA) 계산
        ma_indicator = MovingAverage(period=self.period)
        middle_band = ma_indicator.calculate(chart)
        
        upper_band: List[Optional[Money]] = [None] * len(candles)
        lower_band: List[Optional[Money]] = [None] * len(candles)
        
        # 2. Standard Deviation 및 Upper/Lower Band 계산
        for i in range(self.period - 1, len(candles)):
            # 현재 윈도우의 종가 리스트
            # i번째 포함, 뒤로 period개
            window_slice = candles[i - self.period + 1 : i + 1]
            prices = [float(c.close_price.amount) for c in window_slice]
            
            # 평균 (Middle Band 값)
            mean_val = float(middle_band[i].amount) # type: ignore (middle_band[i] is ensured to be not None by logic)
            
            # 표준편차 계산
            variance = sum([pow(p - mean_val, 2) for p in prices]) / len(prices)
            std_dev = math.sqrt(variance)
            
            # 밴드폭 계산
            bandwidth = std_dev * self.std_dev_multiplier
            
            # 상단/하단 밴드 설정
            currency = candles[i].close_price.currency
            upper_band[i] = Money(amount=Decimal(mean_val + bandwidth), currency=currency)
            lower_band[i] = Money(amount=Decimal(mean_val - bandwidth), currency=currency)
            
        return upper_band, middle_band, lower_band
