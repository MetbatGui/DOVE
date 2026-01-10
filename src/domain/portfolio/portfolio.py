from typing import Dict, List, Optional
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.position import Position

class Portfolio:
    """
    여러 종목의 포지션을 관리하는 애그리거트 루트(Aggregate Root).
    매수/매도 명령을 받아 개별 포지션에 위임하거나 생명주기를 관리합니다.
    """
    def __init__(self):
        self._positions: Dict[str, Position] = {}

    @property
    def positions(self) -> List[Position]:
        """현재 보유중인 모든 포지션 반환"""
        return list(self._positions.values())

    def get_position(self, ticker: Ticker) -> Optional[Position]:
        """특정 종목의 포지션 조회"""
        return self._positions.get(ticker.code)

    def buy(self, ticker: Ticker, quantity: Decimal, price: Money):
        """
        매수: 포지션이 있으면 추가 매수(평단 재계산), 없으면 신규 생성
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        position = self.get_position(ticker)
        
        if position:
            position.increase(quantity, price)
        else:
            self._positions[ticker.code] = Position(ticker, quantity, price)

    def sell(self, ticker: Ticker, quantity: Optional[Decimal] = None):
        """
        매도: 수량 차감. 전량 매도 시 포트폴리오에서 제거.
        quantity가 None이면 전량 매도.
        """
        position = self.get_position(ticker)
        if not position:
            raise ValueError(f"Position not found for ticker: {ticker.code}")

        # None이면 전량 매도
        if quantity is None:
            quantity = position.quantity
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        position.decrease(quantity)
        
        # 잔고가 0이 되면 포지션 삭제
        if position.quantity == 0:
            del self._positions[ticker.code]
