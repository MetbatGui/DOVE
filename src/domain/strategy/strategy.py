from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import date
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.trading_signal import TradingSignal

class Strategy(ABC):
    """
    매매 전략 인터페이스.
    전체 시장 데이터를 분석하여 종목별 매매 신호(Signal)를 생성합니다.
    """
    
    @abstractmethod
    def analyze(self, universe_data: Dict[str, CandleChart], current_date: date) -> Dict[str, TradingSignal]:
        """
        특정 시점(current_date)의 시장 데이터를 분석하여 종목별 신호를 반환합니다.
        
        Args:
            universe_data: {ticker_code: chart} 형태의 전체 시장 데이터
            current_date: 현재 분석 시점
            
        Returns:
            {ticker_code: signal} 형태의 종목별 매매 신호 맵
        """
        pass
