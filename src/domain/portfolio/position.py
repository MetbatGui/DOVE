from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money

class Position:
    """
    개별 종목의 보유 포지션을 나타내는 엔티티.
    보유 수량과 평단가(Average Price)를 관리합니다.
    """
    def __init__(self, ticker: Ticker, quantity: Decimal, average_price: Money):
        if quantity <= 0:
            raise ValueError("Initial quantity must be positive")
        
        self.ticker = ticker
        self._quantity = quantity
        self._average_price = average_price

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def average_price(self) -> Money:
        return self._average_price

    @property
    def total_amount(self) -> Money:
        """총 평가금액 (평단가 기준)"""
        return self._average_price * self._quantity

    def increase(self, quantity: Decimal, price: Money):
        """
        추가 매수: 수량 증가 및 평단가 재계산 (이동평균법)
        New Avg = (Old Total + New Total) / (Old Qty + New Qty)
        """
        if quantity <= 0:
            raise ValueError("Quantity to increase must be positive")
        
        if price.currency != self._average_price.currency:
            raise ValueError("Currency mismatch")

        # 기존 총액 + 신규 매수 총액
        new_amount = price * quantity
        total_value = self.total_amount + new_amount
        
        # 전체 수량 업데이트
        self._quantity += quantity
        
        # 평단가 재계산
        # Money 나누기 Decimal 지원 필요 (Money 클래스 확인 필요, 만약 지원 안하면 amount로 계산)
        # Money / Decimal 연산 지원 가정하거나 amount로 계산 후 새 Money 생성
        self._average_price = Money(amount=total_value.amount / self._quantity, currency=self._average_price.currency)

    def decrease(self, quantity: Decimal):
        """
        매도: 수량 감소 (평단가는 변하지 않음)
        """
        if quantity <= 0:
            raise ValueError("Quantity to decrease must be positive")
        if quantity > self._quantity:
            raise ValueError("Insufficient quantity")

        self._quantity -= quantity
