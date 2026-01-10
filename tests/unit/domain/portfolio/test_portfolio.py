import pytest
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio

class TestPortfolio:
    def setup_method(self):
        self.pf = Portfolio()
        self.samsung = Ticker("005930", "삼성전자")
        self.sk = Ticker("000660", "SK하이닉스")

    def test_buy_new_position(self):
        """신규 종목 매수 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        pos = self.pf.get_position(self.samsung)
        assert pos is not None
        assert pos.quantity == Decimal(10)
        assert pos.average_price == Money.krw(50000)

    def test_buy_existing_position(self):
        """기존 종목 추가 매수(물타기/불타기) 테스트"""
        # 1차: 10주 @ 50,000
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        # 2차: 10주 @ 60,000
        # 총 20주, 총액 1,100,000 => 평단 55,000
        self.pf.buy(self.samsung, Decimal(10), Money.krw(60000))
        
        pos = self.pf.get_position(self.samsung)
        assert pos.quantity == Decimal(20)
        assert pos.average_price == Money.krw(55000)

    def test_sell_partial(self):
        """부분 매도 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        self.pf.sell(self.samsung, Decimal(4))
        
        pos = self.pf.get_position(self.samsung)
        assert pos.quantity == Decimal(6)
        assert pos.average_price == Money.krw(50000)

    def test_sell_full(self):
        """전량 매도(포지션 정리) 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        self.pf.sell(self.samsung, Decimal(10))
        
        pos = self.pf.get_position(self.samsung)
        assert pos is None
        assert len(self.pf.positions) == 0

    def test_sell_non_existent(self):
        """없는 종목 매도 시 예외 발생"""
        with pytest.raises(ValueError, match="Position not found"):
            self.pf.sell(self.sk, Decimal(1))

    def test_multiple_positions(self):
        """여러 종목 관리 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        self.pf.buy(self.sk, Decimal(5), Money.krw(100000))
        
        assert len(self.pf.positions) == 2
        
        self.pf.sell(self.samsung, Decimal(10))
        assert len(self.pf.positions) == 1
        assert self.pf.get_position(self.sk) is not None
