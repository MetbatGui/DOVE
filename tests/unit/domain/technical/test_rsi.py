import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.rsi import RSI

class TestRSI:
    def setup_method(self):
        self.ticker = Ticker(code="005930", name="삼성전자")
        self.unit = CandleUnit.day()
        self.base_time = datetime(2023, 1, 1, 9, 0)

    def _create_chart(self, prices: list[int]) -> CandleChart:
        chart = CandleChart(self.ticker, self.unit)
        for i, price in enumerate(prices):
            c = Candle(
                Money.krw(price), Money.krw(price), Money.krw(price), Money.krw(price), 100,
                self.base_time + timedelta(days=i)
            )
            chart.add_candle(c)
        return chart

    def test_rsi_insufficient_data(self):
        """데이터가 period보다 적거나 같으면 결과는 모두 None이어야 함"""
        rsi = RSI(period=14)
        prices = [100] * 14
        chart = self._create_chart(prices)
        
        result = rsi.calculate(chart)
        assert len(result) == 14
        assert all(x is None for x in result)

    def test_rsi_calculation_manual_short_period(self):
        """짧은 기간(2)으로 정확한 값 계산 검증"""
        # Prices: 100 -> 110 -> 105 -> 115
        # Diffs:   +10    -5     +10
        # U:       10     0      10
        # D:       0      5      0
        rsi = RSI(period=2)
        prices = [100, 110, 105, 115]
        chart = self._create_chart(prices)
        
        result = rsi.calculate(chart)
        
        # Index 0, 1: None (Need 2 data points for diffs? No.
        # Diffs start from index 1. 2 diffs needed for Period=2.
        # Diffs indices: 0(from price 0->1), 1(from price 1->2).
        # So we need 3 price points to get 2 diffs.
        # Result[0]: None
        # Result[1]: None (First diff covers result[1]? No.
        # Diffs needed: [10, 0] for first avg. 
        # Diff index 0 is price[1]-price[0].
        # Diff index 1 is price[2]-price[1].
        # SMA uses diffs[:period=2]. So diffs[0], diffs[1].
        # This gives RSI for price[2] (Candle index 2).
        
        assert result[0] is None
        assert result[1] is None
        
        # Index 2 Calculation:
        # avg_u = (10 + 0) / 2 = 5
        # avg_d = (0 + 5) / 2 = 2.5
        # RS = 5 / 2.5 = 2.0
        # RSI = 100 - 100/(1+2) = 66.666...
        assert result[2] is not None
        assert abs(result[2] - 66.666666) < 0.001
        
        # Index 3 Calculation (Wilder):
        # Current U=10, D=0
        # avg_u = (5 * 1 + 10) / 2 = 7.5
        # avg_d = (2.5 * 1 + 0) / 2 = 1.25
        # RS = 7.5 / 1.25 = 6.0
        # RSI = 100 - 100/(1+6) = 85.714...
        assert result[3] is not None
        assert abs(result[3] - 85.714285) < 0.001

    def test_rsi_all_up_trend(self):
        """지속 상승 시 RSI 100"""
        rsi = RSI(period=2)
        prices = [100, 110, 120, 130, 140]
        chart = self._create_chart(prices)
        result = rsi.calculate(chart)
        
        # Index 2, 3, 4 should be 100.0
        for i in range(2, 5):
            assert result[i] == 100.0

    def test_rsi_all_down_trend(self):
        """지속 하락 시 RSI 0"""
        rsi = RSI(period=2)
        prices = [100, 90, 80, 70, 60]
        chart = self._create_chart(prices)
        result = rsi.calculate(chart)
        
        for i in range(2, 5):
            assert result[i] == 0.0

    def test_rsi_flat(self):
        """변동 없을 시 처리 (현재 로직상 RSI 100으로 처리됨)"""
        # avg_d가 0이므로 division by zero 방지로 100 반환
        rsi = RSI(period=2)
        prices = [100, 100, 100, 100]
        chart = self._create_chart(prices)
        result = rsi.calculate(chart)
        
        assert result[2] == 100.0
        assert result[3] == 100.0
