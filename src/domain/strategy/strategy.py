from abc import ABC, abstractmethod
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.trading_signal import TradingSignal

class Strategy(ABC):
    """
    매매 전략 인터페이스.
    차트 데이터를 분석하여 매매 신호(Signal)를 생성합니다.
    """
    
    @abstractmethod
    def analyze(self, chart: CandleChart, current_index: int) -> TradingSignal:
        """
        차트의 특정 시점(current_index)을 기준으로 분석하여 신호를 반환합니다.
        
        Args:
            chart: 분석 대상 캔들 차트 (전체 데이터)
            current_index: 현재 시뮬레이션 중인 캔들의 인덱스
            
        Returns:
            TradingSignal: 매수/매도/관망 신호
        """
        pass
