import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.ema import EMA

class TestEMA:
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

    def test_ema_insufficient_data(self):
        ema = EMA(period=5)
        prices = [1000] * 4
        chart = self._create_chart(prices)
        
        results = ema.calculate(chart)
        assert len(results) == 4
        assert all(r is None for r in results)

    def test_ema_calculation(self):
        """EMA 계산 검증"""
        # Period = 2, k = 2/(2+1) = 2/3 = 0.666...
        ema = EMA(period=2)
        prices = [10, 20, 30, 40]
        # Index 0: 10
        # Index 1: 20 -> Initial SMA = (10+20)/2 = 15
        # Index 2: 30 -> EMA = (30 - 15) * 2/3 + 15 = 15 * 0.666 + 15 = 10 + 15 = 25
        # Index 3: 40 -> EMA = (40 - 25) * 2/3 + 25 = 15 * 0.666 + 25 = 10 + 25 = 35
        
        chart = self._create_chart(prices)
        results = ema.calculate(chart)
        
        assert results[0] is None
        assert results[1].amount == Decimal("15.0") # SMA
        
        # 소수점 계산 오차 고려 (Decimal 사용이므로 정확해야 하지만 float 변환 오자 주의)
        # 25.0
        assert abs(results[2].amount - Decimal("25.0")) < Decimal("0.001")
        # 35.0
        assert abs(results[3].amount - Decimal("35.0")) < Decimal("0.001")
