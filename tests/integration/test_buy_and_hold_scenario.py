import pytest
from datetime import date
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.application.service.backtest_service import BacktestService
from src.infrastructure.market.pykrx_data_provider import PyKrxDataProvider
from src.domain.strategy.presets.buy_and_hold_strategy import BuyAndHoldStrategy

class TestBuyAndHoldScenario:
    """
    Buy & Hold 전략에 대한 통합 테스트 시나리오.
    2025년 삼성전자 데이터를 사용하여 실제 백테스트 흐름을 검증합니다.
    """
    
    def setup_method(self):
        self.data_provider = PyKrxDataProvider()
        self.backtest_service = BacktestService(self.data_provider)
        
    def test_samsung_2025_buy_and_hold(self):
        # Arrange
        ticker = Ticker(code="005930", name="삼성전자")
        strategy = BuyAndHoldStrategy()
        
        # 2026년 현재 시점에서 2025년은 과거 데이터이므로 조회 가능
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)
        initial_capital = Money.krw(100_000_000) # 1억원
        
        # Act
        result = self.backtest_service.run(
            [ticker],
            strategy,
            start_date,
            end_date,
            initial_capital
        )
        
        # Assert
        # 1. 기본 정보 검증
        assert result.ticker.code == ticker.code
        assert result.initial_capital == initial_capital
        assert len(result.daily_equity_curve) > 200 # 1년치 영업일 데이터 존재 확인
        
        # 2. 매매 동작 검증
        # Buy & Hold이므로 초반에 매수가 발생했어야 함
        assert len(result.trade_logs) >= 1
        first_trade = result.trade_logs[0]
        assert first_trade.action == "BUY"
        assert "Always Buy" in first_trade.reason
        
        # 3. 자산 변화 검증
        # 1년 보유했으므로 자산 가치에 변동이 있어야 함 (0% 수익률일 확률은 극히 낮음)
        assert result.total_return != 0.0
        
        # 4. 결과 출력 (디버깅 및 리포트용)
        print(f"\n[Test Result] Samsung 2025 Buy&Hold")
        print(f"Final Equity: {result.final_equity}")
        print(f"Return: {result.total_return * 100:.2f}%")
        print(f"MDD: {result.mdd * 100:.2f}%")
        print(f"Total Trades: {len(result.trade_logs)}")
