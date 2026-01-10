import pytest
from datetime import date
from src.domain.market.ticker import Ticker
from src.infrastructure.market.pykrx_data_provider import PyKrxDataProvider
from src.domain.market.candle_chart import CandleChart

class TestPyKrxDataProvider:
    def setup_method(self):
        self.provider = PyKrxDataProvider()
        self.ticker = Ticker(code="005930", name="삼성전자")

    def test_get_ohlcv_returns_candle_chart(self):
        """실제 데이터 조회 및 CandleChart 변환 검증"""
        start_date = date(2025, 12, 12)
        end_date = date(2025, 12, 26)
        
        chart = self.provider.get_ohlcv(self.ticker, start_date, end_date)
        
        # 1. 타입 검증
        assert isinstance(chart, CandleChart)
        assert chart.ticker.code == "005930"
        
        # 2. 데이터 존재 여부 검증
        assert len(chart) > 0
        
        # 3. 데이터 정합성 검증 (알려진 값)
        # 2025-12-12 종가 108,900원, 12-26 종가 117,000원
        first_candle = chart.candles[0]
        last_candle = chart.candles[-1]
        
        # 날짜 확인
        assert first_candle.timestamp.date() == start_date or first_candle.timestamp.date() > start_date
        assert last_candle.timestamp.date() == end_date or last_candle.timestamp.date() < end_date
        
        # 가격 확인 (Money.amount는 Decimal)
        # 단순히 0보다 큰지, 그리고 대략적인 범위인지 확인해도 충분하지만, 여기선 특정일 값을 아니까 확인
        # 주의: pykrx 데이터가 휴일 등으로 인해 start_date와 정확히 일치하지 않을 수 있음.
        # 따라서 특정 날짜를 찾아서 검증하는 것이 더 안전함.
        
        target_candle = next((c for c in chart.candles if c.timestamp.date() == date(2025, 12, 12)), None)
        assert target_candle is not None
        assert target_candle.close_price.amount == 108900
        
        target_candle_last = next((c for c in chart.candles if c.timestamp.date() == date(2025, 12, 26)), None)
        assert target_candle_last is not None
        assert target_candle_last.close_price.amount == 117000
