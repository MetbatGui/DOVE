import pytest
from datetime import datetime, timedelta
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money

class TestCandleChartValidation:
    def setup_method(self):
        self.ticker = Ticker(code="005930", name="삼성전자")
        self.unit = CandleUnit.day()
        self.krw_1000 = Money.krw(1000)
        self.base_time = datetime(2023, 1, 1, 9, 0)
    
    def _create_candle(self, time_offset_days: int) -> Candle:
        return Candle(open_price=self.krw_1000, high_price=self.krw_1000, low_price=self.krw_1000, close_price=self.krw_1000, volume=100, timestamp=self.base_time + timedelta(days=time_offset_days)
        )

    def test_validate_empty_chart(self):
        """빈 차트 검증"""
        chart = CandleChart(self.ticker, self.unit)
        messages = chart.verify()
        assert len(messages) == 1
        assert "empty" in messages[0]

    def test_validate_normal_chart(self):
        """정상 차트 검증 (주말 포함해도 Gap이 3일+2일=5일 이내라면 정상)"""
        chart = CandleChart(self.ticker, self.unit)
        chart.add_candle(self._create_candle(0)) # 일요일
        chart.add_candle(self._create_candle(1)) # 월요일
        chart.add_candle(self._create_candle(2)) # 화요일
        
        # 1일 간격이므로 정상
        messages = chart.verify()
        assert len(messages) == 0

    def test_validate_gap_detection(self):
        """Gap 검출 테스트"""
        chart = CandleChart(self.ticker, self.unit)
        chart.add_candle(self._create_candle(0)) 
        chart.add_candle(self._create_candle(10)) # 10일 후 (Gap 발생해야 함)

        messages = chart.verify()
        assert len(messages) == 1
        assert "[Gap]" in messages[0]
        assert "Missing data" in messages[0]

    def test_validate_duplicate_order(self):
        """순서/중복 오류 검출 (강제 삽입 시)"""
        # add_candle은 정렬을 보장하므로, 내부 리스트를 강제로 조작하여 테스트
        chart = CandleChart(self.ticker, self.unit)
        c1 = self._create_candle(0)
        c2 = self._create_candle(1)
        
        # 정상 추가
        chart.add_candle(c1)
        chart.add_candle(c2)
        
        # 강제로 순서 변경 (테스트 목적)
        # _candles는 private이지만 테스트를 위해 접근
        chart._candles[0], chart._candles[1] = chart._candles[1], chart._candles[0]
        
        messages = chart.verify()
        assert len(messages) > 0
        assert "[Order/Duplicate]" in messages[0]
