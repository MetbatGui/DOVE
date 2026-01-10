from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator
from src.domain.shared.money import Money

class Candle(BaseModel):
    """
    OHLCV (Open, High, Low, Close, Volume) 데이터를 표현하는 도메인 모델.
    Pydantic을 사용하여 자동 타입 검증 및 데이터 무결성 검증 지원.
    """
    open_price: Money
    high_price: Money
    low_price: Money
    close_price: Money
    volume: int
    timestamp: datetime

    model_config = {
        "frozen": True,  # 불변성 유지
    }

    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """거래량 검증"""
        if v < 0:
            raise ValueError("Volume cannot be negative")
        return v

    @model_validator(mode='after')
    def validate_ohlc(self):
        """OHLC 논리 검증"""
        # 1. 통화 일치 검증
        currency = self.open_price.currency
        if not (self.high_price.currency == currency and 
                self.low_price.currency == currency and 
                self.close_price.currency == currency):
            raise ValueError("All prices must have the same currency")

        # 2. 고가는 모든 가격보다 크거나 같아야 함
        if not (self.high_price >= self.open_price and 
                self.high_price >= self.low_price and 
                self.high_price >= self.close_price):
            raise ValueError("High price must be the highest among OHLC")

        # 3. 저가는 모든 가격보다 작거나 같아야 함
        if not (self.low_price <= self.open_price and 
                self.low_price <= self.high_price and 
                self.low_price <= self.close_price):
            raise ValueError("Low price must be the lowest among OHLC")
        
        return self

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
        return Money(amount=total_amount / 4, currency=self.open_price.currency)

    def __hash__(self) -> int:
        """Pydantic BaseModel은 기본적으로 해시 불가능하므로 명시적 구현"""
        return hash((
            self.open_price, self.high_price, self.low_price,
            self.close_price, self.volume, self.timestamp
        ))

    def __str__(self) -> str:
        return (f"Candle(Time={self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"O={self.open_price}, H={self.high_price}, "
                f"L={self.low_price}, C={self.close_price}, V={self.volume})")
