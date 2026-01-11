from decimal import Decimal
import pytest
from datetime import datetime, timedelta
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.technical.bollinger_bands import BollingerBands
from src.domain.shared.money import Money
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.ticker import Ticker

class TestBollingerBands:
    def _create_chart(self, prices: list[float]) -> CandleChart:
        ticker = Ticker(code="005930", name="Test Ticker")
        candles = []
        base_date = datetime(2023, 1, 1)
        for i, price in enumerate(prices):
            candles.append(Candle(
                timestamp=base_date + timedelta(days=i),
                open_price=Money.krw(price),
                high_price=Money.krw(price),
                low_price=Money.krw(price),
                close_price=Money.krw(price),
                volume=100
            ))
        return CandleChart(ticker=ticker, unit=CandleUnit.day(), candles=candles)

    def test_bollinger_bands_calculation(self):
        # 20일치 데이터 생성 (편의상 1~20)
        # 1~20의 평균 = 10.5
        # 분산 = sum((x - 10.5)^2) / 20 = 33.25
        # 표준편차 = sqrt(33.25) ≈ 5.76628
        # Upper = 10.5 + (2 * 5.76628) = 10.5 + 11.53256 = 22.03256
        # Lower = 10.5 - 11.53256 = -1.03256
        
        prices = [float(i) for i in range(1, 21)]
        chart = self._create_chart(prices)
        
        bb = BollingerBands(period=20, std_dev_multiplier=2.0)
        upper, middle, lower = bb.calculate(chart)
        
        assert len(upper) == 20
        assert upper[18] is None # 19일까지는 데이터 부족 (0-indexed 18 = 19번째)
        
        last_idx = 19
        assert middle[last_idx].amount == Decimal("10.5")
        
        # 허용 오차 범위 내 근사값 비교
        assert abs(float(upper[last_idx].amount) - 22.03256) < 0.0001
        assert abs(float(lower[last_idx].amount) - (-1.03256)) < 0.0001
        
        # 항상 Upper >= Middle >= Lower
        assert upper[last_idx].amount >= middle[last_idx].amount >= lower[last_idx].amount

    def test_insufficient_data(self):
        prices = [100.0] * 10 
        chart = self._create_chart(prices)
        
        bb = BollingerBands(period=20)
        upper, middle, lower = bb.calculate(chart)
        
        assert all(v is None for v in upper)
        assert all(v is None for v in middle)
        assert all(v is None for v in lower)
