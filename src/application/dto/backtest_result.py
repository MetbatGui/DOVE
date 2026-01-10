from typing import List, Dict
from decimal import Decimal
from pydantic import BaseModel
from src.domain.shared.money import Money
from src.domain.market.ticker import Ticker

class TradeLog(BaseModel):
    """
    거래 로그 DTO.
    Pydantic을 사용하여 자동 타입 검증 지원.
    """
    date: str
    action: str  # "BUY" or "SELL"
    quantity: Decimal
    price: Money
    amount: Money
    reason: str = ""

    model_config = {
        "frozen": True,
    }

    def __hash__(self) -> int:
        return hash((self.date, self.action, self.quantity, self.price, self.amount, self.reason))

class BacktestResult(BaseModel):
    """
    백테스트 결과 DTO.
    Pydantic을 사용하여 자동 타입 검증 및 JSON 직렬화 지원.
    """
    ticker: Ticker
    total_return: float  # 수익률 (ex: 0.15 = 15%)
    final_equity: Money  # 최종 자산 평가액
    initial_capital: Money  # 초기 자본금
    mdd: float  # Maximum Drawdown (ex: -0.2 = -20%)
    trade_logs: List[TradeLog] = []
    daily_equity_curve: Dict[str, float] = {}

    model_config = {
        "frozen": True,
    }

    @property
    def profit_amount(self) -> Money:
        """수익금"""
        return self.final_equity - self.initial_capital

    def __hash__(self) -> int:
        return hash((
            self.ticker, self.total_return, self.final_equity,
            self.initial_capital, self.mdd, tuple(self.trade_logs)
        ))

    def __str__(self) -> str:
        return (f"BacktestResult(Ticker={self.ticker.code}, "
                f"Return={self.total_return:.2%}, "
                f"Final={self.final_equity}, "
                f"MDD={self.mdd:.2%}, Trades={len(self.trade_logs)})")
