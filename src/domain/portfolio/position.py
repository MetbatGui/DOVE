from decimal import Decimal
from pydantic import BaseModel, Field
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money

class Position(BaseModel):
    """
    개별 종목의 보유 포지션을 나타내는 엔티티.
    보유 수량과 평단가(Average Price)를 관리합니다.
    Pydantic을 사용하여 데이터 검증.
    """
    ticker: Ticker
    quantity: Decimal = Field(ge=0)
    average_price: Money

    model_config = {
        "frozen": False,  # 상태 변경 가능
        "validate_assignment": True, # 값 변경 시에도 검증
    }

    @property
    def total_amount(self) -> Money:
        """총 평가금액 (평단가 기준)"""
        return self.average_price * self.quantity

    def increase(self, quantity: Decimal, price: Money):
        """
        추가 매수: 수량 증가 및 평단가 재계산 (이동평균법)
        New Avg = (Old Total + New Total) / (Old Qty + New Qty)
        """
        if quantity <= 0:
            raise ValueError("Quantity to increase must be positive")
        
        if price.currency != self.average_price.currency:
            raise ValueError("Currency mismatch")

        # 기존 총액 + 신규 매수 총액
        new_amount = price * quantity
        total_value = self.total_amount + new_amount
        
        # 전체 수량 업데이트
        self.quantity += quantity
        
        # 평단가 재계산
        self.average_price = Money(amount=total_value.amount / self.quantity, currency=self.average_price.currency)

    def decrease(self, quantity: Decimal):
        """
        매도: 수량 감소 (평단가는 변하지 않음)
        """
        if quantity <= 0:
            raise ValueError("Quantity to decrease must be positive")
        if quantity > self.quantity:
            raise ValueError("Insufficient quantity")

        self.quantity -= quantity
