import pytest
from datetime import date
from decimal import Decimal
from typing import Dict
from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.strategy import Strategy
from src.domain.strategy.trading_signal import TradingSignal, SignalType
from src.application.service.backtest_service import BacktestService
from src.infrastructure.market.pykrx_data_provider import PyKrxDataProvider

class BuyAndHoldStrategy(Strategy):
    """
    첫 날 매수하고 계속 보유하는 단순 전략 (Multi-Asset 호환).
    """
    def analyze(self, universe_data: Dict[str, CandleChart], current_date: date) -> Dict[str, TradingSignal]:
        signals: Dict[str, TradingSignal] = {}
        
        for ticker_code, chart in universe_data.items():
            # 첫 번째 캔들(index=0)일 때만 매수
            # 이를 위해 날짜 인덱스를 찾음
            idx = chart.find_index_by_date(current_date)
            if idx == 0:
                signal = TradingSignal(
                    type=SignalType.BUY, 
                    ticker=chart.ticker, 
                    reason="Buy and Hold Init"
                )
                signals[ticker_code] = signal
            else:
                signal = TradingSignal(
                    type=SignalType.HOLD, 
                    ticker=chart.ticker
                )
                signals[ticker_code] = signal
                
        return signals

class TestBacktestService:
    def setup_method(self):
        self.provider = PyKrxDataProvider()
        self.service = BacktestService(self.provider)
        self.ticker = Ticker(code="005930", name="삼성전자")
        self.start_date = date(2025, 1, 1)
        self.end_date = date(2025, 12, 31) # 2025년 1년치
        self.initial_capital = Money.krw(10_000_000) # 1000만원

    def test_run_buy_and_hold(self):
        """Buy & Hold 전략 백테스트 검증"""
        strategy = BuyAndHoldStrategy()
        
        # Multi-Asset 지원을 위해 list로 전달
        result = self.service.run(
            [self.ticker], 
            strategy, 
            self.start_date, 
            self.end_date, 
            self.initial_capital
        )
        
        # 1. 결과 타입 검증
        assert result.ticker.code == self.ticker.code
        assert result.initial_capital == self.initial_capital
        
        # 2. 거래 내역 검증 (Buy 1회)
        assert len(result.trade_logs) == 1
        assert result.trade_logs[0].action == "BUY"
        assert result.trade_logs[0].reason == "Buy and Hold Init"
        
        # 3. 자산 변화 검증
        # 2025년 1월 2일(영업일) 매수 -> 12월 30일(폐장일) 평가
        # 수익률이 0이 아님을 확인 (상승하든 하락하든 변동이 있어야 함)
        assert result.total_return != 0.0
        
        # MDD가 계산되었는지 확인
        assert result.mdd <= 0.0
        
        print(f"\n[Backtest Result] Ticker: {result.ticker.name}")
        print(f"Total Return: {result.total_return * 100:.2f}%")
        print(f"Final Equity: {result.final_equity}")
        print(f"MDD: {result.mdd * 100:.2f}%")
