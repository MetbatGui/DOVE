from dataclasses import dataclass, field
from typing import List, Dict
from decimal import Decimal
from src.domain.shared.money import Money
from src.domain.market.ticker import Ticker

@dataclass
class TradeLog:
    """개별 거래 기록"""
    date: str
    action: str  # BUY, SELL
    quantity: Decimal
    price: Money
    amount: Money
    reason: str = ""

@dataclass
class BacktestResult:
    """백테스트 결과 리포트"""
    ticker: Ticker
    total_return: float  # 수익률 (ex: 0.15 = 15%)
    final_equity: Money  # 최종 자산 평가액 (현금 + 주식평가액)
    initial_capital: Money # 초기 자본금
    mdd: float # Maximum Drawdown (ex: -0.2 = -20%)
    trade_logs: List[TradeLog] = field(default_factory=list)
    daily_equity_curve: Dict[str, float] = field(default_factory=dict) # 날짜별 자산 추이

    @property
    def profit_amount(self) -> Money:
        """수익금"""
        return self.final_equity - self.initial_capital
