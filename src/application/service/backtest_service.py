from datetime import date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from src.domain.market.ticker import Ticker
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio
from src.domain.strategy.strategy import Strategy
from src.domain.strategy.trading_signal import TradingSignal, SignalType
from src.ports.market_data_provider import MarketDataProvider
from src.application.dto.backtest_result import BacktestResult, TradeLog

class BacktestService:
    """
    백테스트 시뮬레이션을 수행하는 애플리케이션 서비스.
    Multi-Asset 지원을 위해 날짜 기반의 순회 로직을 사용합니다.
    """
    TRANSACTION_COST_RATE = Decimal("0.003")  # 거래 비용률 (0.3%)
    
    def __init__(self, data_provider: MarketDataProvider):
        self.data_provider = data_provider

    def run(self, tickers: List[Ticker], strategy: Strategy, start_date: date, end_date: date, initial_capital: Money) -> BacktestResult:
        """
        백테스트 실행
        
        Args:
            tickers: 백테스트할 종목 리스트
            strategy: 매매 전략 (Multi-Asset 지원)
            start_date: 시작일
            end_date: 종료일
            initial_capital: 초기 자금
            
        Returns:
            BacktestResult: 백테스트 결과 (현재는 첫 번째 종목 기준 리포트 반환)
        """
        # 1. 데이터 준비 (Universe 생성)
        universe: Dict[str, CandleChart] = {}
        all_dates = set()
        
        for ticker in tickers:
            chart = self.data_provider.get_ohlcv(ticker, start_date, end_date)
            # 데이터가 없는 종목은 제외
            if not chart.candles:
                continue
            
            universe[ticker.code] = chart
            # 차트의 모든 날짜 수집
            for candle in chart.candles:
                all_dates.add(candle.timestamp.date())
        
        if not universe:
            raise ValueError("No data found for any ticker in the given range.")
            
        # 날짜 정렬
        sorted_dates = sorted(list(all_dates))

        # 2. 초기화
        portfolio = Portfolio(initial_capital)
        trade_logs: List[TradeLog] = []
        daily_equity_curve: Dict[str, float] = {}
        mdd_tracker = {"peak": initial_capital.amount, "max_drawdown": Decimal(0)}

        # 3. 시뮬레이션 루프 (시간 기반)
        for current_date in sorted_dates:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 3.1 전략 분석 (전체 시장 데이터 제공)
            signals = strategy.analyze(universe, current_date)
            
            # 3.2 매매 실행
            # 리밸런싱을 위해 매도(현금확보) 먼저, 그 다음 매수 실행
            
            # 매도 시그널 처리 - 보유 중인 종목에 대해 SELL 시그널이 있으면 처리
            sell_signals = [s for s in signals.values() if s.type == SignalType.SELL]
            for signal in sell_signals:
                if not signal.ticker: # Ticker 정보 필수
                    continue
                
                # 해당 날짜의 캔들 데이터 찾기 (가격 정보 필요)
                chart = universe.get(signal.ticker.code)
                if not chart: continue
                
                idx = chart.find_index_by_date(current_date)
                if idx == -1: continue # 오늘 데이터 없으면 거래 불가
                
                candle = chart.candles[idx]
                trade_log = self._execute_trade(signal.ticker, portfolio, candle, signal, date_str)
                if trade_log:
                    trade_logs.append(trade_log)

            # 매수 시그널 처리
            buy_signals = [s for s in signals.values() if s.type == SignalType.BUY]
            for signal in buy_signals:
                if not signal.ticker:
                    continue
                
                chart = universe.get(signal.ticker.code)
                if not chart: continue
                
                idx = chart.find_index_by_date(current_date)
                if idx == -1: continue
                
                candle = chart.candles[idx]
                trade_log = self._execute_trade(signal.ticker, portfolio, candle, signal, date_str)
                if trade_log:
                    trade_logs.append(trade_log)
            
            # 3.3 일별 자산 평가 및 MDD 계산
            # 현재 유니버스에 있는 모든 종목의 오늘 종가 수집
            current_prices = {}
            for ticker_code, chart in universe.items():
                idx = chart.find_index_by_date(current_date)
                if idx != -1:
                    current_prices[ticker_code] = chart.candles[idx].close_price
            
            total_equity = self._evaluate_portfolio(portfolio, current_prices)
            daily_equity_curve[date_str] = float(total_equity.amount)
            self._update_mdd(total_equity.amount, mdd_tracker)
            
        # 4. 결과 생성
        # BacktestResult가 단일 Ticker를 요구하므로, 일단 대표(첫번째) Ticker를 넘기거나 수정 필요.
        # 여기서는 첫 번째 Ticker를 넘기도록 유지 (DTO 수정 최소화)
        representative_ticker = tickers[0] if tickers else Ticker(code="MULTI", name="Multi Asset")
        
        return self._create_result(
            representative_ticker, initial_capital, daily_equity_curve, 
            trade_logs, mdd_tracker["max_drawdown"]
        )
    
    def _execute_trade(
        self, 
        ticker: Ticker, 
        portfolio: Portfolio, 
        candle: Candle, 
        signal: TradingSignal,
        date_str: str
    ) -> Optional[TradeLog]:
        """
        매매 신호에 따라 거래 실행
        """
        current_price = candle.close_price
        
        if signal.type == SignalType.BUY:
            return self._execute_buy(ticker, portfolio, current_price, signal, date_str)
        elif signal.type == SignalType.SELL:
            return self._execute_sell(ticker, portfolio, current_price, signal, date_str)
        
        return None
    
    def _execute_buy(
        self,
        ticker: Ticker,
        portfolio: Portfolio,
        price: Money,
        signal: TradingSignal,
        date_str: str
    ) -> Optional[TradeLog]:
        """매수 실행"""
        if portfolio.cash.amount <= 0:
            return None
        
        quantity = self._calculate_buy_quantity(portfolio, price, signal.quantity)
        if quantity <= 0:
            return None
        
        try:
            portfolio.buy(ticker, quantity, price)
            return self._create_buy_log(date_str, quantity, price, signal.reason)
        except ValueError:
            # 현금 부족 등으로 매수 실패
            return None
    
    def _execute_sell(
        self,
        ticker: Ticker,
        portfolio: Portfolio,
        price: Money,
        signal: TradingSignal,
        date_str: str
    ) -> Optional[TradeLog]:
        """매도 실행"""
        position = portfolio.get_position(ticker)
        if not position:
            return None
        
        quantity = self._calculate_sell_quantity(position.quantity, signal.quantity)
        if quantity <= 0:
            return None
        
        try:
            portfolio.sell(ticker, price, quantity)
            return self._create_sell_log(date_str, quantity, price, signal.reason)
        except ValueError:
            # 수량 부족 등으로 매도 실패
            return None
    
    def _calculate_buy_quantity(
        self, 
        portfolio: Portfolio, 
        price: Money, 
        signal_quantity: Optional[Decimal]
    ) -> Decimal:
        """매수 수량 계산"""
        if signal_quantity is not None:
            return signal_quantity
        
        # 거래 비용을 고려한 최대 매수 수량
        total_rate = Decimal(1) + self.TRANSACTION_COST_RATE
        return Decimal(int(portfolio.cash.amount / (price.amount * total_rate)))
    
    def _calculate_sell_quantity(
        self, 
        position_quantity: Decimal, 
        signal_quantity: Optional[Decimal]
    ) -> Decimal:
        """매도 수량 계산"""
        if signal_quantity is None:
            return position_quantity
        
        # 보유량보다 많이 팔 수 없음
        return min(signal_quantity, position_quantity)
    
    def _create_buy_log(
        self, 
        date_str: str, 
        quantity: Decimal, 
        price: Money, 
        reason: str
    ) -> TradeLog:
        """매수 거래 로그 생성"""
        stock_cost = price * quantity
        transaction_fee = stock_cost * self.TRANSACTION_COST_RATE
        total_cost = stock_cost + Money(amount=transaction_fee.amount, currency=price.currency)
        
        return TradeLog(
            date=date_str,
            action="BUY",
            quantity=quantity,
            price=price,
            amount=total_cost,
            reason=reason
        )
    
    def _create_sell_log(
        self, 
        date_str: str, 
        quantity: Decimal, 
        price: Money, 
        reason: str
    ) -> TradeLog:
        """매도 거래 로그 생성"""
        gross_revenue = price * quantity
        transaction_fee = gross_revenue * self.TRANSACTION_COST_RATE
        net_revenue = gross_revenue - Money(amount=transaction_fee.amount, currency=price.currency)
        
        return TradeLog(
            date=date_str,
            action="SELL",
            quantity=quantity,
            price=price,
            amount=net_revenue,
            reason=reason
        )
    
    def _evaluate_portfolio(
        self, 
        portfolio: Portfolio, 
        current_prices: Dict[str, Money]
    ) -> Money:
        """
        포트폴리오 자산 평가
        
        Args:
            portfolio: 포트폴리오
            current_prices: {ticker_code: price} 형태의 현재가 딕셔너리
            
        Returns:
            Money: 총 자산 (현금 + 주식 평가액)
        """
        return portfolio.get_total_equity(current_prices)
    
    def _update_mdd(self, current_equity: Decimal, mdd_tracker: Dict[str, Decimal]) -> None:
        """MDD(Maximum Drawdown) 업데이트"""
        if current_equity > mdd_tracker["peak"]:
            mdd_tracker["peak"] = current_equity
        
        drawdown = (mdd_tracker["peak"] - current_equity) / mdd_tracker["peak"] if mdd_tracker["peak"] > 0 else Decimal(0)
        if drawdown > mdd_tracker["max_drawdown"]:
            mdd_tracker["max_drawdown"] = drawdown
    
    def _create_result(
        self,
        ticker: Ticker,
        initial_capital: Money,
        daily_equity_curve: Dict[str, float],
        trade_logs: List[TradeLog],
        max_drawdown: Decimal
    ) -> BacktestResult:
        """백테스트 결과 객체 생성"""
        final_equity = Money.krw(list(daily_equity_curve.values())[-1]) if daily_equity_curve else initial_capital
        total_return = float((final_equity.amount - initial_capital.amount) / initial_capital.amount)
        
        return BacktestResult(
            ticker=ticker,
            total_return=total_return,
            final_equity=final_equity,
            initial_capital=initial_capital,
            mdd=float(max_drawdown) * -1,
            trade_logs=trade_logs,
            daily_equity_curve=daily_equity_curve
        )
