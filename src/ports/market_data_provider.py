from abc import ABC, abstractmethod
from datetime import date
from src.domain.market.ticker import Ticker
from src.domain.market.candle_chart import CandleChart

class MarketDataProvider(ABC):
    """
    시장 데이터(OHLCV)를 제공하는 포트(Port) 인터페이스.
    외부 데이터 소스(pykrx, yfinance 등)와의 의존성을 분리합니다.
    """
    
    @abstractmethod
    def get_ohlcv(self, ticker: Ticker, start_date: date, end_date: date) -> CandleChart:
        """
        특정 종목의 기간별 OHLCV 데이터를 조회하여 도메인 객체(CandleChart)로 반환합니다.
        
        Args:
            ticker: 조회할 종목
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            CandleChart: 조회된 캔들 차트 데이터
        """
        pass
