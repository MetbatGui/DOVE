import pytest
from datetime import datetime
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.moving_average import MovingAverage

class TestMovingAverage:
    def setup_method(self):
        self.ticker = Ticker("005930", "삼성전자")
        self.unit = CandleUnit.minute(5)
        self.chart = CandleChart(self.ticker, self.unit)
        
        # 테스트용 데이터: 1000, 2000, 3000, 4000, 5000 ...
        base_time = datetime(2023, 1, 1, 9, 0)
        self.prices = [1000, 2000, 3000, 4000, 5000]
        for i, price in enumerate(self.prices):
            money = Money.krw(price)
            candle = Candle(money, money, money, money, 100, 
                          datetime.fromtimestamp(base_time.timestamp() + i * 300))
            self.chart.add_candle(candle)

    def test_init_validation(self):
        """초기화 값 검증"""
        with pytest.raises(ValueError):
            MovingAverage(0)
        with pytest.raises(ValueError):
            MovingAverage(-5)

    def test_calculate_sma_basic(self):
        """기본적인 SMA 계산 (기간 3)"""
        ma = MovingAverage(period=3)
        result = ma.calculate(self.chart)

        # 입력 데이터: [1000, 2000, 3000, 4000, 5000]
        # 예상 결과:
        # idx 0: None (데이터 부족)
        # idx 1: None (데이터 부족)
        # idx 2: (1000+2000+3000)/3 = 2000
        # idx 3: (2000+3000+4000)/3 = 3000
        # idx 4: (3000+4000+5000)/3 = 4000

        assert len(result) == 5
        assert result[0] is None
        assert result[1] is None
        assert result[2] == Money.krw(2000)
        assert result[3] == Money.krw(3000)
        assert result[4] == Money.krw(4000)

    def test_calculate_not_enough_data(self):
        """데이터가 기간보다 적을 때 테스트"""
        ma = MovingAverage(period=10) # 데이터는 5개뿐
        result = ma.calculate(self.chart)

        assert len(result) == 5
        assert all(r is None for r in result)

    def test_calculate_exact_data(self):
        """데이터 개수와 기간이 같을 때 테스트"""
        ma = MovingAverage(period=5)
        result = ma.calculate(self.chart)

        assert len(result) == 5
        assert result[0] is None
        assert result[3] is None
        # 마지막 하나만 계산됨: (1000+2000+3000+4000+5000)/5 = 3000
        assert result[4] == Money.krw(3000)
