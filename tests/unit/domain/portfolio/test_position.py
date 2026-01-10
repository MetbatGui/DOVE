import pytest
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.position import Position

class TestPosition:
    def setup_method(self):
        self.ticker = Ticker("005930", "삼성전자")

    def test_init_validation(self):
        """초기 수량 검증"""
        with pytest.raises(ValueError):
            Position(self.ticker, Decimal(0), Money.krw(100))
        
        with pytest.raises(ValueError):
            Position(self.ticker, Decimal(-1), Money.krw(100))

    def test_increase_average_price(self):
        """매수 시 평단가 계산 검증"""
        # 초기: 10주 @ 10,000원 = 100,000원
        pos = Position(self.ticker, Decimal(10), Money.krw(10000))
        
        # 추가: 10주 @ 20,000원 = 200,000원
        # 총: 20주, 300,000원 => 평단 15,000원
        pos.increase(Decimal(10), Money.krw(20000))
        
        assert pos.quantity == Decimal(20)
        assert pos.average_price == Money.krw(15000)

    def test_decrease_quantity(self):
        """매도 시 수량만 감소하고 평단가는 유지"""
        pos = Position(self.ticker, Decimal(10), Money.krw(10000))
        
        pos.decrease(Decimal(3))
        
        assert pos.quantity == Decimal(7)
        assert pos.average_price == Money.krw(10000)

    def test_decrease_validation(self):
        """매도 수량 검증"""
        pos = Position(self.ticker, Decimal(10), Money.krw(10000))
        
        # 보유량 초과 매도 시도
        with pytest.raises(ValueError, match="Insufficient quantity"):
            pos.decrease(Decimal(11))
            
        # 음수/0 매도 시도
        with pytest.raises(ValueError):
            pos.decrease(Decimal(0))

    def test_increase_decimal_quantity(self):
        """소수점 수량에 대한 평단가 계산 검증"""
        # 1.5주 @ 1000원 = 1500원
        pos = Position(self.ticker, Decimal("1.5"), Money.krw(1000))
        
        # 0.5주 @ 2000원 = 1000원
        pos.increase(Decimal("0.5"), Money.krw(2000))
        
        # 총: 2.0주, 2500원 => 평단 1250원
        assert pos.quantity == Decimal("2.0")
        assert pos.average_price == Money.krw(1250)
