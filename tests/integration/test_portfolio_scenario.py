import pytest
from datetime import datetime
from decimal import Decimal
from pykrx import stock
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio

class TestPortfolioScenario:
    def setup_method(self):
        self.ticker = Ticker("005930", "삼성전자")
        self.pf = Portfolio()
        
        # 통합 테스트용 데이터 기간 (2025-12-12 ~ 2025-12-26)
        start_date = "20251212"
        end_date = "20251226"
        self.df = stock.get_market_ohlcv(start_date, end_date, self.ticker.code)
        
        # 날짜별 종가 맵핑 (편의상)
        self.prices = {
            d.strftime("%Y%m%d"): int(r['종가']) 
            for d, r in self.df.iterrows()
        }

    def test_scenario_buy_sell_avg_down_pyramid(self):
        """
        시나리오:
        1. 2025-12-12: 최초 매수 (10주)
        2. 2025-12-15: 하락 -> 부분 손절 (3주)
        3. 2025-12-16: 추가 하락 -> 추매(물타기) (5주)
        4. 2025-12-17: 반등 -> 추매(불타기) (5주)
        5. 2025-12-26: 상승 -> 전량 매도
        """
        
        # 1. 2025-12-12: 최초 매수 (10주)
        # 종가: 108,900원 확인 (데이터 정합성 체크)
        price_1 = self.prices["20251212"]
        assert price_1 == 108900
        
        self.pf.buy(self.ticker, Decimal(10), Money.krw(price_1))
        
        pos = self.pf.get_position(self.ticker)
        assert pos.quantity == Decimal(10)
        assert pos.average_price == Money.krw(108900)
        
        # 2. 2025-12-15: 하락 -> 부분 손절 (3주)
        # 종가: 104,800원 (약 -3.7% 손실 구간)
        price_2 = self.prices["20251215"]
        assert price_2 == 104800
        
        self.pf.sell(self.ticker, Decimal(3))
        
        pos = self.pf.get_position(self.ticker)
        assert pos.quantity == Decimal(7)
        assert pos.average_price == Money.krw(108900) # 평단가는 변하지 않음
        
        # 3. 2025-12-16: 추가 하락 -> 물타기 (5주)
        # 종가: 102,800원
        price_3 = self.prices["20251216"]
        assert price_3 == 102800
        
        self.pf.buy(self.ticker, Decimal(5), Money.krw(price_3))
        
        # 평단가 계산: 
        # 기존: 7주 * 108,900 = 762,300
        # 신규: 5주 * 102,800 = 514,000
        # 총: 12주, 1,276,300 => 106,358.333... -> 106,358 (Money는 소수점 버림/반올림 정책에 따르지만 현재 로직상 float 계산 후 Money 생성)
        # Money 생성 시점에 Decimal로 변환됨.
        
        pos = self.pf.get_position(self.ticker)
        assert pos.quantity == Decimal(12)
        
        # 정확한 계산 검증 (오차 범위 고려 없이 정확히 떨어지는지 확인)
        expected_avg = (Decimal(108900 * 7) + Decimal(102800 * 5)) / Decimal(12)
        # Money 내부적으로 Decimal을 쓰므로 정밀 비교 가능
        assert pos.average_price.amount == expected_avg
        
        # 4. 2025-12-17: 반등 -> 불타기 (5주)
        # 종가: 107,900원
        price_4 = self.prices["20251217"]
        assert price_4 == 107900
        
        self.pf.buy(self.ticker, Decimal(5), Money.krw(price_4))
        
        # 평단가 계산:
        # 기존: 12주 (총액 1,276,300)
        # 신규: 5주 * 107,900 = 539,500
        # 총: 17주, 1,815,800 => 106,811.7647...
        
        pos = self.pf.get_position(self.ticker)
        assert pos.quantity == Decimal(17)
        
        expected_total = Decimal(1276300) + Decimal(107900 * 5)
        expected_avg_2 = expected_total / Decimal(17)
        
        assert pos.average_price.amount == expected_avg_2
        
        # 5. 2025-12-26: 상승 -> 전량 매도 (quantity=None 사용)
        # 종가: 117,000원
        price_5 = self.prices["20251226"]
        assert price_5 == 117000
        
        self.pf.sell(self.ticker)
        
        pos = self.pf.get_position(self.ticker)
        assert pos is None
        assert len(self.pf.positions) == 0
