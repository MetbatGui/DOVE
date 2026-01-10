import pytest
from datetime import datetime
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money

class TestCandleChart:
    def setup_method(self):
        self.ticker = Ticker("005930", "삼성전자")
        self.unit = CandleUnit.minute(5)
        self.krw_1000 = Money.krw(1000)
        self.timestamp1 = datetime(2023, 1, 1, 9, 0)
        self.timestamp2 = datetime(2023, 1, 1, 9, 5)
        
        self.candle1 = Candle(self.krw_1000, self.krw_1000, self.krw_1000, self.krw_1000, 100, self.timestamp1)
        self.candle2 = Candle(self.krw_1000, self.krw_1000, self.krw_1000, self.krw_1000, 200, self.timestamp2)

    def test_init_candle_chart(self):
        """차트 초기화 테스트"""
        chart = CandleChart(self.ticker, self.unit)
        assert chart.ticker == self.ticker
        assert chart.unit == self.unit
        assert len(chart) == 0

    def test_add_candle_sorting(self):
        """캔들 추가 및 정렬 테스트"""
        chart = CandleChart(self.ticker, self.unit)
        # 순서 섞어서 추가
        chart.add_candle(self.candle2)
        chart.add_candle(self.candle1)

        assert len(chart) == 2
        # 시간순 정렬 확인
        assert chart[0] == self.candle1
        assert chart[1] == self.candle2

    def test_duplicate_candle_error(self):
        """중복 시간 캔들 추가 시 에러 테스트"""
        chart = CandleChart(self.ticker, self.unit, [self.candle1])
        
        # 동일한 시간의 캔들(내용을 조금 바꿔서)
        duplicate_candle = Candle(self.krw_1000, self.krw_1000, self.krw_1000, self.krw_1000, 300, self.timestamp1)
        
        with pytest.raises(ValueError, match="already exists"):
            chart.add_candle(duplicate_candle)

    def test_get_latest_candle(self):
        """최신 캔들 조회 테스트"""
        chart = CandleChart(self.ticker, self.unit)
        assert chart.get_latest_candle() is None

        chart.add_candle(self.candle1)
        assert chart.get_latest_candle() == self.candle1

        chart.add_candle(self.candle2)
        assert chart.get_latest_candle() == self.candle2

    def test_getitem_and_iter(self):
        """리스트처럼 접근 테스트"""
        chart = CandleChart(self.ticker, self.unit, [self.candle1, self.candle2])
        
        assert chart[0] == self.candle1
        assert chart[-1] == self.candle2
        
        candles = [c for c in chart]
        assert len(candles) == 2
        assert candles[0] == self.candle1
