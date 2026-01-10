from dataclasses import dataclass
from datetime import datetime
from src.domain.shared.money import Money

@dataclass(frozen=True)
class Candle:
    """
    OHLCV (Open, High, Low, Close, Volume) 데이터를 표현하는 도메인 모델입니다.
    기본적인 데이터 무결성 검증과 캔들 패턴 판별 로직을 포함합니다.
    """
    open_price: Money
    high_price: Money
    low_price: Money
    close_price: Money
    volume: int
    timestamp: datetime

    def __post_init__(self):
        # 1. 통화 일치 검증
        currency = self.open_price.currency
        if not (self.high_price.currency == currency and 
                self.low_price.currency == currency and 
                self.close_price.currency == currency):
            raise ValueError("All prices must have the same currency")

        # 2. 거래량 검증
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

        # 3. OHLC 논리 검증
        # 고가는 시가, 저가, 종가보다 크거나 같아야 함
        if not (self.high_price >= self.open_price and 
                self.high_price >= self.low_price and 
                self.high_price >= self.close_price):
            raise ValueError("High price must be the highest among OHLC")

        # 저가는 시가, 고가, 종가보다 작거나 같아야 함
        if not (self.low_price <= self.open_price and 
                self.low_price <= self.high_price and 
                self.low_price <= self.close_price):
            raise ValueError("Low price must be the lowest among OHLC")

    @property
    def is_bullish(self) -> bool:
        """양봉 여부 (종가 > 시가)"""
        return self.close_price > self.open_price

    @property
    def is_bearish(self) -> bool:
        """음봉 여부 (종가 < 시가)"""
        return self.close_price < self.open_price
    
    @property
    def is_doji(self) -> bool:
        """도지 여부 (종가 == 시가)"""
        return self.close_price == self.open_price

    @property
    def average_price(self) -> Money:
        """OHLC 평균가 계산"""
        total_amount = (self.open_price.amount + self.high_price.amount + 
                       self.low_price.amount + self.close_price.amount)
        # Money 객체의 __mul__ 로직 활용 (Decimal 처리는 Money 내부에서 담당)
        return Money(total_amount / 4, self.open_price.currency)

    def __str__(self) -> str:
        return (f"Candle(Time={self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"O={self.open_price}, H={self.high_price}, "
                f"L={self.low_price}, C={self.close_price}, V={self.volume})")
