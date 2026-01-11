from abc import ABC, abstractmethod
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.trading_signal import TradingSignal

class AssetEvaluator(ABC):
    """
    개별 자산(Single Asset)을 분석하여 매매 신호를 생성하는 인터페이스.
    """

    @abstractmethod
    def evaluate(self, chart: CandleChart, current_index: int) -> TradingSignal:
        """
        특정 종목의 차트를 분석하여 매매 신호 또는 평가 결과를 반환합니다.
        
        Args:
            chart: 분석할 종목의 차트 데이터 (CandleChart)
            current_index: 현재 시뮬레이션 시점의 인덱스
            
        Returns:
            TradingSignal: 매수/매도/관망 신호
        """
        pass
