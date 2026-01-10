from datetime import date
from pykrx import stock
from src.domain.market.ticker import Ticker
from src.domain.market.candle_chart import CandleChart
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.shared.money import Money
from src.ports.market_data_provider import MarketDataProvider

class PyKrxDataProvider(MarketDataProvider):
    """
    pykrx 라이브러리를 사용하여 시장 데이터를 제공하는 구현체.
    """
    def get_ohlcv(self, ticker: Ticker, start_date: date, end_date: date) -> CandleChart:
        # pykrx 요구 포맷: "YYYYMMDD"
        s_date_str = start_date.strftime("%Y%m%d")
        e_date_str = end_date.strftime("%Y%m%d")
        
        # 데이터 조회 (Dataframe 반환)
        df = stock.get_market_ohlcv(s_date_str, e_date_str, ticker.code)
        
        # 도메인 객체로 변환
        chart = CandleChart(ticker, CandleUnit.day()) # 일단 일봉 고정
        
        for timestamp, row in df.iterrows():
            candle = Candle(
                open_price=Money.krw(row['시가']),
                high_price=Money.krw(row['고가']),
                low_price=Money.krw(row['저가']),
                close_price=Money.krw(row['종가']),
                volume=int(row['거래량']),
                timestamp=timestamp
            )
            chart.add_candle(candle)
            
        return chart
