from typing import Dict, List, Optional
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.position import Position

class Portfolio:
    """
    여러 종목의 포지션과 현금을 관리하는 애그리거트 루트(Aggregate Root).
    
    실제 증권 계좌처럼 동작하며:
    - 현금(cash) 관리
    - 매수/매도 시 거래 비용 자동 처리 (수수료 + 슬리피지)
    - 총 자산 평가 기능
    """
    def __init__(
        self, 
        initial_cash: Money,
        commission_rate: Decimal = Decimal("0.002"),  # 0.2% 수수료
        slippage_rate: Decimal = Decimal("0.001")     # 0.1% 슬리피지
    ):
        """
        Args:
            initial_cash: 초기 현금 (예수금)
            commission_rate: 거래 수수료율 (기본값: 0.2%)
            slippage_rate: 슬리피지율 (기본값: 0.1%)
        """
        if commission_rate < 0 or slippage_rate < 0:
            raise ValueError("Commission and slippage rates must be non-negative")
        
        self._cash = initial_cash
        self._commission_rate = commission_rate
        self._slippage_rate = slippage_rate
        self._positions: Dict[str, Position] = {}

    @property
    def cash(self) -> Money:
        """현재 보유 현금"""
        return self._cash
    
    @property
    def positions(self) -> List[Position]:
        """현재 보유중인 모든 포지션 반환"""
        return list(self._positions.values())

    def get_position(self, ticker: Ticker) -> Optional[Position]:
        """특정 종목의 포지션 조회"""
        return self._positions.get(ticker.code)

    def buy(self, ticker: Ticker, quantity: Decimal, price: Money):
        """
        매수: 주식 비용 + 거래 비용을 현금에서 차감하고 포지션 추가/업데이트
        
        Args:
            ticker: 매수할 종목
            quantity: 매수 수량
            price: 매수 가격
            
        Raises:
            ValueError: 수량이 0 이하이거나 현금이 부족한 경우
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # 거래 비용 계산
        stock_cost = price * quantity
        transaction_fee = Money(
            stock_cost.amount * (self._commission_rate + self._slippage_rate),
            price.currency
        )
        total_cost = stock_cost + transaction_fee
        
        # 현금 확인
        if total_cost > self._cash:
            raise ValueError(
                f"Insufficient cash: need {total_cost}, have {self._cash}"
            )
        
        # 현금 차감
        self._cash -= total_cost
        
        # 포지션 추가/업데이트
        position = self.get_position(ticker)
        if position:
            position.increase(quantity, price)
        else:
            self._positions[ticker.code] = Position(ticker, quantity, price)

    def sell(self, ticker: Ticker, price: Money, quantity: Optional[Decimal] = None):
        """
        매도: 포지션 감소 및 매도 대금 - 거래 비용을 현금에 추가
        
        Args:
            ticker: 매도할 종목
            price: 매도 가격 (거래 비용 계산에 필요)
            quantity: 매도 수량 (None이면 전량 매도)
            
        Raises:
            ValueError: 포지션이 없거나 수량이 부족한 경우
        """
        position = self.get_position(ticker)
        if not position:
            raise ValueError(f"Position not found for ticker: {ticker.code}")

        # None이면 전량 매도
        if quantity is None:
            quantity = position.quantity
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if quantity > position.quantity:
            raise ValueError(
                f"Insufficient quantity: have {position.quantity}, trying to sell {quantity}"
            )

        # 거래 비용 계산
        gross_revenue = price * quantity
        transaction_fee = Money(
            gross_revenue.amount * (self._commission_rate + self._slippage_rate),
            price.currency
        )
        net_revenue = gross_revenue - transaction_fee
        
        # 현금 증가
        self._cash += net_revenue
        
        # 포지션 감소
        position.decrease(quantity)
        
        # 잔고가 0이 되면 포지션 삭제
        if position.quantity == 0:
            del self._positions[ticker.code]
    
    def get_total_equity(self, current_prices: Dict[str, Money]) -> Money:
        """
        총 자산 평가 = 현금 + 모든 포지션의 평가액
        
        Args:
            current_prices: {ticker_code: current_price} 딕셔너리
            
        Returns:
            Money: 총 자산 가치
        """
        position_value = Money(Decimal(0), self._cash.currency)
        
        for position in self.positions:
            current_price = current_prices.get(position.ticker.code)
            if current_price:
                position_value += current_price * position.quantity
        
        return self._cash + position_value
