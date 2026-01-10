from enum import Enum
from decimal import Decimal
from typing import Union
from pydantic import BaseModel, Field, field_validator

class Currency(str, Enum):
    KRW = "KRW"
    USD = "USD"

    def __str__(self):
        return self.value

class Money(BaseModel):
    """
    금액을 나타내는 값 객체 (Value Object).
    Pydantic을 사용하여 자동 타입 검증 및 변환 지원.
    """
    amount: Decimal
    currency: Currency

    model_config = {
        "frozen": True,  # 불변성 유지
    }

    @staticmethod
    def krw(amount: Union[int, float, Decimal, str]) -> 'Money':
        """KRW 통화로 Money 인스턴스 생성 (팩토리 메서드)"""
        return Money(amount=Decimal(str(amount)), currency=Currency.KRW)

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: Union[int, float, Decimal]) -> 'Money':
        if not isinstance(factor, (int, float, Decimal)):
            raise TypeError(f"Multiplier must be a number, not {type(factor)}")
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        return self < other or self == other

    def __gt__(self, other: 'Money') -> bool:
        return not (self <= other)

    def __ge__(self, other: 'Money') -> bool:
        return not (self < other)

    def __str__(self) -> str:
        if self.currency == Currency.KRW:
            return f"{int(self.amount):,}원"
        return f"{self.currency} {self.amount:,.2f}"
    
    def __hash__(self) -> int:
        """Pydantic BaseModel은 기본적으로 해시 불가능하므로 명시적 구현"""
        return hash((self.amount, self.currency))
