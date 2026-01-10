from enum import Enum
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class SignalType(str, Enum):
    """매매 신호 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

    def __str__(self):
        return self.value

class TradingSignal(BaseModel):
    """
    매매 신호를 나타내는 DTO.
    Pydantic을 사용하여 자동 타입 검증 지원.
    """
    type: SignalType
    quantity: Optional[Decimal] = None
    reason: str = ""

    model_config = {
        "frozen": True,  # 불변성 유지
    }

    @classmethod
    def buy(cls, quantity: Optional[Decimal] = None, reason: str = "") -> 'TradingSignal':
        """매수 신호 생성"""
        return cls(type=SignalType.BUY, quantity=quantity, reason=reason)

    @classmethod
    def sell(cls, quantity: Optional[Decimal] = None, reason: str = "") -> 'TradingSignal':
        """매도 신호 생성"""
        return cls(type=SignalType.SELL, quantity=quantity, reason=reason)

    @classmethod
    def hold(cls, reason: str = "") -> 'TradingSignal':
        """보유 신호 생성"""
        return cls(type=SignalType.HOLD, quantity=None, reason=reason)

    def __hash__(self) -> int:
        """Pydantic BaseModel은 기본적으로 해시 불가능하므로 명시적 구현"""
        return hash((self.type, self.quantity, self.reason))

    def __str__(self) -> str:
        qty_str = f"Qty={self.quantity}" if self.quantity else "Qty=All"
        return f"Signal({self.type}, {qty_str}, Reason={self.reason})"
