from typing import List, Optional
from decimal import Decimal
from src.domain.technical.indicator import Indicator
from src.domain.market.candle_chart import CandleChart

class RSI(Indicator):
    """
    RSI (Relative Strength Index) 지표 구현체
    Wilder's Smoothing 방식을 사용하여 계산합니다.
    """
    def __init__(self, period: int = 14):
        if period < 1:
            raise ValueError("Period must be at least 1")
        self.period = period

    def calculate(self, chart: CandleChart) -> List[Optional[float]]:
        candles = chart.candles
        if len(candles) <= self.period:
            return [None] * len(candles)

        # 1. 등락폭(Diff) 계산
        # diffs[i] = candles[i+1].close - candles[i].close
        # 데이터 포인트: 0일에 대한 diff는 없음. 1일부터 시작.
        closes = [float(c.close_price.amount) for c in candles]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        # U(Up), D(Down) 분리
        ups = [x if x > 0 else 0.0 for x in deltas]
        downs = [-x if x < 0 else 0.0 for x in deltas]

        rsi_values: List[Optional[float]] = [None] * len(candles)

        # 2. 초기 평균 (SMA): 첫 period 동안의 평균
        # deltas 인덱스 0 ~ period-1 (총 period 개) 사용 => 캔들 인덱스로는 1 ~ period
        # 따라서 첫 RSI 값은 index = period 일 때 산출됨
        
        avg_u = sum(ups[:self.period]) / self.period
        avg_d = sum(downs[:self.period]) / self.period

        # 첫 번째 RSI 계산 (index = period)
        rs = avg_u / avg_d if avg_d != 0 else 0
        if avg_d == 0:
            rsi_values[self.period] = 100.0
        else:
            rsi_values[self.period] = 100.0 - (100.0 / (1.0 + rs))

        # 3. Wilder's Smoothing 적용 (Calculated iteratively)
        # index i는 period+1 부터 끝까지 (즉, deltas의 인덱스 period 부터)
        for i in range(self.period, len(deltas)):
            current_up = ups[i]
            current_down = downs[i]

            # 이전 평균값 사용
            avg_u = (avg_u * (self.period - 1) + current_up) / self.period
            avg_d = (avg_d * (self.period - 1) + current_down) / self.period

            if avg_d == 0:
                rsi_val = 100.0
            elif avg_u == 0: # avg_d != 0
                rsi_val = 0.0
            else:
                rs = avg_u / avg_d
                rsi_val = 100.0 - (100.0 / (1.0 + rs))
            
            # deltas[i]는 candles[i+1]의 변동분이므로, rsi값은 candles[i+1]에 매핑
            candle_idx = i + 1
            rsi_values[candle_idx] = rsi_val

        return rsi_values
