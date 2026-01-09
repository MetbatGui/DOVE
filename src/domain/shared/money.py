from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from typing import Union

class Currency(str, Enum):
    KRW = "KRW"
    USD = "USD"

    def __str__(self):
        return self.value

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self):
        # Ensure calculated amount is Decimal
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

    @staticmethod
    def krw(amount: Union[int, float, Decimal, str]) -> 'Money':
        return Money(amount, Currency.KRW)

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Union[int, float, Decimal]) -> 'Money':
        if not isinstance(factor, (int, float, Decimal)):
            raise TypeError(f"Multiplier must be a number, not {type(factor)}")
        return Money(self.amount * Decimal(str(factor)), self.currency)

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
