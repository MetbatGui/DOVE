from abc import ABC, abstractmethod
from typing import Any
from src.domain.market.candle_chart import CandleChart

class Indicator(ABC):
    """
    모든 기술적 지표의 기본이 되는 추상 클래스입니다.
    """
    
    @abstractmethod
    def calculate(self, chart: CandleChart) -> Any:
        """
        주어진 캔들 차트를 기반으로 지표를 계산합니다.
        
        Args:
            chart: 계산 대상 캔들 차트
            
        Returns:
            계산된 지표 결과 (지표마다 반환 타입이 다를 수 있음)
        """
        pass
