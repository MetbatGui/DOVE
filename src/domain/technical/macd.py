from typing import List, Dict, Optional
from pydantic import BaseModel, model_validator, PrivateAttr
from src.domain.technical.indicator import Indicator
from src.domain.market.candle_chart import CandleChart
from src.domain.technical.ema import EMA

class MACD(BaseModel, Indicator):
    """
    MACD (Moving Average Convergence Divergence) 지표
    Pydantic을 사용하여 설정 검증.
    """
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

    _fast_ema: EMA = PrivateAttr()
    _slow_ema: EMA = PrivateAttr()

    def model_post_init(self, __context):
        self._fast_ema = EMA(period=self.fast_period)
        self._slow_ema = EMA(period=self.slow_period)

    @model_validator(mode='after')
    def validate_periods(self):
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")
        return self

    def calculate(self, chart: CandleChart) -> List[Dict[str, Optional[float]]]:
        """
        MACD, Signal, Histogram을 계산합니다.
        
        Returns:
            List[Dict]: [{'macd': float, 'signal': float, 'histogram': float}, ...]
        """
        candles = chart.candles
        if len(candles) < self.slow_period:
            # 적어도 slow_period만큼은 있어야 MACD가 나옴
            return [{'macd': None, 'signal': None, 'histogram': None}] * len(candles)

        # 1. Fast, Slow EMA 계산
        fast_values = self._fast_ema.calculate(chart)
        slow_values = self._slow_ema.calculate(chart)
        
        results: List[Dict[str, Optional[float]]] = []
        macd_line_values = []

        # MACD Line 계산
        for i in range(len(candles)):
            f_val = fast_values[i]
            s_val = slow_values[i]
            
            current_result = {'macd': None, 'signal': None, 'histogram': None}
            
            if f_val is None or s_val is None:
                macd_line_values.append(None)
            else:
                macd_val = float(f_val.amount - s_val.amount)
                current_result['macd'] = macd_val
                macd_line_values.append(macd_val)
            
            results.append(current_result)

        # 2. Signal Line 계산 (MACD Line의 EMA)
        # EMA 클래스는 CandleChart를 입력으로 받지만, 여기서는 숫자 리스트(macd_line)를 입력으로 받아야 함.
        # EMA 클래스를 재사용하기 어렵다면 (CandleChart 의존성 때문에), EMA 로직을 분리하거나 직접 계산해야 함.
        # 여기서는 내부적으로 간단한 EMA 로직을 구현하여 사용 (Signal Line용)
        
        signal_line_values = self._calculate_signal_ema(macd_line_values, self.signal_period)
        
        # 3. Histogram 및 최종 결과 병합
        for i in range(len(candles)):
            macd_val = macd_line_values[i]
            signal_val = signal_line_values[i]
            
            if macd_val is not None and signal_val is not None:
                results[i]['macd'] = macd_val
                results[i]['signal'] = signal_val
                results[i]['histogram'] = macd_val - signal_val
            else:
                # macd만 있고 signal이 없는 구간 (초기 signal_period 동안)
                if macd_val is not None:
                     results[i]['macd'] = macd_val
    
        return results

    def _calculate_signal_ema(self, values: List[Optional[float]], period: int) -> List[Optional[float]]:
        # None이 섞여있는 리스트의 EMA 계산
        # 유효한 값이 period개 모인 시점부터 SMA -> EMA 전환
        
        results = [None] * len(values)
        valid_values = []
        first_valid_idx = -1
        
        for i, val in enumerate(values):
            if val is not None:
                if first_valid_idx == -1:
                    first_valid_idx = i
                valid_values.append(val)
        
        if len(valid_values) < period:
            return results

        # period만큼의 초기 데이터로 SMA 계산
        initial_sma = sum(valid_values[:period]) / period
        
        # results에 SMA 값 할당 (index = first_valid_idx + period - 1)
        start_cal_idx = first_valid_idx + period - 1
        results[start_cal_idx] = initial_sma

        # EMA 계산
        k = 2.0 / (period + 1.0)
        prev_ema = initial_sma
        
        # valid_values의 period 이후부터 순회
        # 매핑되는 원본 인덱스를 잘 찾아야 함
        
        # 이미 계산된 initial_sma 다음부터
        current_valid_idx = period 
        
        for i in range(start_cal_idx + 1, len(values)):
             val = values[i]
             if val is None:
                 continue
                 
             # EMA = (Close - Prev) * k + Prev
             ema = (val * k) + (prev_ema * (1 - k))
             results[i] = ema
             prev_ema = ema

        return results
