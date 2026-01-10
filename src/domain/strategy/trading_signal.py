from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from src.domain.shared.money import Money

class SignalType(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()

@dataclass(frozen=True)
class TradingSignal:
    """
    전략(Strategy)이 생성하는 매매 신호.
    """
    type: SignalType
    price: Optional[Money] = None  # 지정가 주문 시 필요, None이면 시장가(혹은 종가)
    quantity: Optional[Decimal] = None # 주문 수량, None이면 기본 정책 따름 (ex: 전량 매수/매도)
    reason: str = "" # 로깅용

    @classmethod
    def buy(cls, price: Optional[Money] = None, quantity: Optional[Decimal] = None, reason: str = "") -> 'TradingSignal':
        return cls(SignalType.BUY, price, quantity, reason)

    @classmethod
    def sell(cls, price: Optional[Money] = None, quantity: Optional[Decimal] = None, reason: str = "") -> 'TradingSignal':
        return cls(SignalType.SELL, price, quantity, reason)

    @classmethod
    def hold(cls, reason: str = "") -> 'TradingSignal':
        return cls(SignalType.HOLD, price=None, quantity=None, reason=reason)
