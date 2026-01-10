import pytest
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio

class TestPortfolio:
    def setup_method(self):
        self.pf = Portfolio(initial_cash=Money.krw(10_000_000))  # 1천만원 초기 자금
        self.samsung = Ticker("005930", "삼성전자")
        self.sk = Ticker("000660", "SK하이닉스")

    def test_initial_cash(self):
        """초기 현금 확인"""
        assert self.pf.cash == Money.krw(10_000_000)

    def test_buy_new_position(self):
        """신규 종목 매수 테스트 (거래 비용 포함)"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        pos = self.pf.get_position(self.samsung)
        assert pos is not None
        assert pos.quantity == Decimal(10)
        assert pos.average_price == Money.krw(50000)
        
        # 거래 비용 확인 (주식 비용 + 0.3% 거래 비용)
        stock_cost = Money.krw(500000)  # 50000 * 10
        transaction_fee = Money.krw(1500)  # 500000 * 0.003
        expected_cash = Money.krw(10_000_000) - stock_cost - transaction_fee
        assert self.pf.cash == expected_cash

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
        """부분 매도 테스트 (거래 비용 포함)"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        cash_after_buy = self.pf.cash
        
        # 4주 매도 @ 60,000
        self.pf.sell(self.samsung, Money.krw(60000), Decimal(4))
        
        pos = self.pf.get_position(self.samsung)
        assert pos.quantity == Decimal(6)
        assert pos.average_price == Money.krw(50000)  # 평단가는 변하지 않음
        
        # 거래 비용 차감 확인
        gross_revenue = Money.krw(240000)  # 60000 * 4
        transaction_fee = Money.krw(720)  # 240000 * 0.003
        net_revenue = gross_revenue - transaction_fee
        expected_cash = cash_after_buy + net_revenue
        assert self.pf.cash == expected_cash

    def test_sell_full_explicit(self):
        """명시적 수량 지정 전량 매도 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        self.pf.sell(self.samsung, Money.krw(55000), Decimal(10))
        
        pos = self.pf.get_position(self.samsung)
        assert pos is None
        assert len(self.pf.positions) == 0

    def test_sell_full_none(self):
        """None 수량(기본값)으로 전량 매도 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        # quantity 인자 생략 시 전량 매도
        self.pf.sell(self.samsung, Money.krw(55000))
        
        pos = self.pf.get_position(self.samsung)
        assert pos is None
        assert len(self.pf.positions) == 0

    def test_sell_non_existent(self):
        """없는 종목 매도 시 예외 발생"""
        with pytest.raises(ValueError, match="Position not found"):
            self.pf.sell(self.sk, Money.krw(100000), Decimal(1))

    def test_insufficient_cash(self):
        """현금 부족 시 매수 불가"""
        with pytest.raises(ValueError, match="Insufficient cash"):
            self.pf.buy(self.samsung, Decimal(1000), Money.krw(50000))  # 5천만원 필요

    def test_multiple_positions(self):
        """여러 종목 관리 테스트"""
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        self.pf.buy(self.sk, Decimal(5), Money.krw(100000))
        
        assert len(self.pf.positions) == 2
        
        self.pf.sell(self.samsung, Money.krw(55000), Decimal(10))
        assert len(self.pf.positions) == 1
        assert self.pf.get_position(self.sk) is not None

    def test_get_total_equity(self):
        """총 자산 평가 테스트"""
        # 삼성전자 10주 매수
        self.pf.buy(self.samsung, Decimal(10), Money.krw(50000))
        
        # 현재가 기준 평가
        current_prices = {
            "005930": Money.krw(60000)  # 주당 1만원 상승
        }
        
        total_equity = self.pf.get_total_equity(current_prices)
        
        # 현금 + 주식 평가액
        # 현금 = 10,000,000 - 500,000 - 1,500(거래비용) = 9,498,500
        # 주식 = 60,000 * 10 = 600,000
        # 총 = 10,098,500
        expected_equity = self.pf.cash + Money.krw(600000)
        assert total_equity == expected_equity

    def test_transaction_cost_calculation(self):
        """거래 비용 정확성 테스트"""
        initial_cash = Money.krw(1_000_000)
        pf = Portfolio(initial_cash)
        
        # 매수
        pf.buy(self.samsung, Decimal(10), Money.krw(10000))
        
        # 예상 비용: 100,000 + 300 (0.3%) = 100,300
        expected_cash_after_buy = Money.krw(899700)
        assert pf.cash == expected_cash_after_buy
        
        # 매도
        pf.sell(self.samsung, Money.krw(12000), Decimal(10))
        
        # 매도 수익: 120,000 - 360 (0.3%) = 119,640
        expected_cash_after_sell = expected_cash_after_buy + Money.krw(119640)
        assert pf.cash == expected_cash_after_sell

