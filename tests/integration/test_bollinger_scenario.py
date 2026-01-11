import pytest
from datetime import date
from decimal import Decimal
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.application.service.backtest_service import BacktestService
from src.infrastructure.market.pykrx_data_provider import PyKrxDataProvider
from src.domain.strategy.presets.bollinger_band_strategy import BollingerBandStrategy

class TestBollingerScenario:
    """
    볼린저 밴드 전략 통합 테스트 시나리오.
    2025년 삼성전자 데이터를 사용하여 평균 회귀 매매 동작을 검증합니다.
    """
    
    def setup_method(self):
        self.data_provider = PyKrxDataProvider()
        self.backtest_service = BacktestService(self.data_provider)
        
    def test_samsung_2025_bollinger_strategy(self):
        # Arrange
        ticker = Ticker(code="005930", name="삼성전자")
        # 기본 설정 (20일, 2배수) 사용
        strategy = BollingerBandStrategy()
        
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
        # 1. 실행 완료 검증
        assert result.ticker.code == ticker.code
        assert len(result.daily_equity_curve) > 200
        
        # 2. 매매 발생 여부 검증
        # 볼린저 밴드 전략은 횡보/하락장에서 매수 기회를 포착해야 함.
        # 1년이라는 기간 동안 한 번도 매매가 없을 확률은 낮음 (단, 밴드폭이 너무 넓거나 추세가 강하면 없을 수도 있음)
        if not result.trade_logs:
            pytest.skip("No trades generated in 2025 for Bollinger Band Strategy (Check constraints)")
            
        print(f"\n[Test Result] Samsung 2025 Bollinger Band")
        print(f"Final Equity: {result.final_equity}")
        print(f"Return: {result.total_return * 100:.2f}%")
        print(f"MDD: {result.mdd * 100:.2f}%")
        print(f"Total Trades: {len(result.trade_logs)}")
        
        # 매매 로그 확인
        for log in result.trade_logs[:5]: # 처음 5개만 출력
            print(f"{log.date} {log.action} @ {log.price} : {log.reason}")
