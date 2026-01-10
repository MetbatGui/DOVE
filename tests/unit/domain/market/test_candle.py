import pytest
from datetime import datetime
from decimal import Decimal
from src.domain.shared.money import Money, Currency
from src.domain.market.candle import Candle

class TestCandle:
    def setup_method(self):
        self.timestamp = datetime(2023, 1, 1, 9, 0)
        self.krw_1000 = Money.krw(1000)
        self.krw_1100 = Money.krw(1100)
        self.krw_900 = Money.krw(900)
        self.krw_1050 = Money.krw(1050)

    def test_create_valid_candle(self):
        """정상적인 캔들 생성 테스트 (양봉)"""
        candle = Candle(
            open_price=self.krw_1000,
            high_price=self.krw_1100,
            low_price=self.krw_900,
            close_price=self.krw_1050,
            volume=100,
            timestamp=self.timestamp
        )
        assert candle.open_price == self.krw_1000
        assert candle.high_price == self.krw_1100
        assert candle.low_price == self.krw_900
        assert candle.close_price == self.krw_1050
        assert candle.volume == 100
        assert candle.timestamp == self.timestamp
        assert candle.is_bullish is True
        assert candle.is_bearish is False

    def test_create_bearish_candle(self):
        """음봉 캔들 테스트"""
        candle = Candle(
            open_price=self.krw_1100,
            high_price=self.krw_1100,
            low_price=self.krw_900,
            close_price=self.krw_1000,
            volume=100,
            timestamp=self.timestamp
        )
        assert candle.is_bullish is False
        assert candle.is_bearish is True
    
    def test_create_doji_candle(self):
        """도지 캔들 테스트"""
        candle = Candle(
            open_price=self.krw_1000,
            high_price=self.krw_1100,
            low_price=self.krw_900,
            close_price=self.krw_1000,
            volume=100,
            timestamp=self.timestamp
        )
        assert candle.is_doji is True
        assert candle.is_bullish is False
        assert candle.is_bearish is False

    def test_validation_currency_mismatch(self):
        """서로 다른 통화 사용 시 에러 발생 테스트"""
        usd_money = Money(Decimal("10.0"), Currency.USD)
        with pytest.raises(ValueError, match="same currency"):
            Candle(
                open_price=self.krw_1000,
                high_price=usd_money,  # 잘못된 통화
                low_price=self.krw_900,
                close_price=self.krw_1000,
                volume=100,
                timestamp=self.timestamp
            )

    def test_validation_negative_volume(self):
        """음수 거래량 테스트"""
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            Candle(
                open_price=self.krw_1000,
                high_price=self.krw_1100,
                low_price=self.krw_900,
                close_price=self.krw_1050,
                volume=-1,
                timestamp=self.timestamp
            )

    def test_validation_invalid_high_price(self):
        """고가가 시가보다 낮은 경우 테스트"""
        with pytest.raises(ValueError, match="High price must be the highest"):
            Candle(
                open_price=self.krw_1000,
                high_price=self.krw_900,  # 고가가 시가보다 낮음
                low_price=self.krw_900,
                close_price=self.krw_1000,
                volume=100,
                timestamp=self.timestamp
            )

    def test_validation_invalid_low_price(self):
        """저가가 시가보다 높은 경우 테스트"""
        krw_1200 = Money.krw(1200)
        krw_1500 = Money.krw(1500)
        with pytest.raises(ValueError, match="Low price must be the lowest"):
            Candle(
                open_price=self.krw_1000,
                high_price=krw_1500,  # 고가를 저가보다 높게 설정하여 첫 번째 검증 통과 
                low_price=krw_1200,   # 저가가 시가/종가보다 높음 -> 에러 발생 예상
                close_price=self.krw_1050,
                volume=100,
                timestamp=self.timestamp
            )

    def test_average_price(self):
        """평균가 계산 테스트"""
        krw_1200 = Money.krw(1200)
        krw_800 = Money.krw(800)
        candle = Candle(
            open_price=self.krw_1000,
            high_price=krw_1200,
            low_price=krw_800,
            close_price=self.krw_1000,
            volume=100,
            timestamp=self.timestamp
        )
        # (1000 + 1200 + 800 + 1000) / 4 = 1000
        assert candle.average_price == self.krw_1000
