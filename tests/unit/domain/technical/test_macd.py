import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.macd import MACD

class TestMACD:
    def setup_method(self):
        self.ticker = Ticker(code="005930", name="삼성전자")
        self.unit = CandleUnit.day()
        self.base_time = datetime(2023, 1, 1, 9, 0)

    def _create_chart(self, prices: list[int]) -> CandleChart:
        chart = CandleChart(self.ticker, self.unit)
        for i, price in enumerate(prices):
            c = Candle(
                open_price=Money.krw(price),
                high_price=Money.krw(price),
                low_price=Money.krw(price),
                close_price=Money.krw(price),
                volume=100,
                timestamp=self.base_time + timedelta(days=i)
            )
            chart.add_candle(c)
        return chart

    def test_macd_insufficient_data(self):
        # Slow period(26)보다 데이터가 적으면 모두 None 반환
        macd = MACD()
        prices = [1000] * 20
        chart = self._create_chart(prices)
        
        results = macd.calculate(chart)
        assert len(results) == 20
        assert all(r['macd'] is None for r in results)

    def test_macd_calculation_short_period(self):
        """짧은 주기로 계산 검증"""
        # Fast=2, Slow=4, Signal=2
        # Data: 10, 20, 30, 40, 50, 60
        prices = [10, 20, 30, 40, 50, 60]
        chart = self._create_chart(prices)
        
        macd = MACD(fast_period=2, slow_period=4, signal_period=2)
        results = macd.calculate(chart)
        
        # 1. EMA Calculation Verification
        # EMA2 (Fast):
        # - Idx 1: SMA (10+20)/2 = 15
        # - Idx 2: (30-15)*2/3 + 15 = 10+15 = 25
        # - Idx 3: (40-25)*2/3 + 25 = 10+25 = 35
        # - Idx 4: (50-35)*2/3 + 35 = 10+35 = 45
        
        # EMA4 (Slow):
        # - Idx 3: SMA (10+20+30+40)/4 = 25
        # - Idx 4: (50-25)*2/5 + 25 = 25*0.4 + 25 = 10+25 = 35
        
        # MACD Line:
        # - Idx 3: EMA2(35) - EMA4(25) = 10
        # - Idx 4: EMA2(45) - EMA4(35) = 10
        
        assert results[3]['macd'] == 10.0
        assert results[4]['macd'] == 10.0
        
        # Signal Line (Signal=2 on MACD Line)
        # MACD values: [None, None, None, 10, 10, ...]
        # Valid MACD starts at index 3.
        # Signal Init SMA (Period 2):
        # - Need MACD at Idx 3 and Idx 4.
        # - SMA = (10 + 10) / 2 = 10
        # - Signal at Idx 4 should be 10.
        
        assert results[3]['signal'] is None
        assert results[4]['signal'] == 10.0
        
        # Histogram
        # - Idx 4: MACD(10) - Signal(10) = 0
        assert results[4]['histogram'] == 0.0

