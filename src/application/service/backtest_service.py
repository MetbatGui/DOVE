from datetime import date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from src.domain.market.ticker import Ticker
from src.domain.market.candle import Candle
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio
from src.domain.strategy.strategy import Strategy
from src.domain.strategy.trading_signal import TradingSignal, SignalType
from src.ports.market_data_provider import MarketDataProvider
from src.application.dto.backtest_result import BacktestResult, TradeLog

class BacktestService:
    """
    백테스트 시뮬레이션을 수행하는 애플리케이션 서비스.
    """
    TRANSACTION_COST_RATE = Decimal("0.003")  # 거래 비용률 (0.3%)
    
    def __init__(self, data_provider: MarketDataProvider):
        self.data_provider = data_provider

    def run(self, ticker: Ticker, strategy: Strategy, start_date: date, end_date: date, initial_capital: Money) -> BacktestResult:
        """
        백테스트 실행
        
        Args:
            ticker: 백테스트할 종목
            strategy: 매매 전략
            start_date: 시작일
            end_date: 종료일
            initial_capital: 초기 자금
            
        Returns:
            BacktestResult: 백테스트 결과
        """
        # 1. 데이터 준비
        chart = self.data_provider.get_ohlcv(ticker, start_date, end_date)
        if not chart.candles:
            raise ValueError("No data found for the given range.")

        # 2. 초기화
        portfolio = Portfolio(initial_capital)
        trade_logs: List[TradeLog] = []
        daily_equity_curve: Dict[str, float] = {}
        mdd_tracker = {"peak": initial_capital.amount, "max_drawdown": Decimal(0)}

        # 3. 시뮬레이션 루프
        for i, candle in enumerate(chart.candles):
            date_str = candle.timestamp.strftime("%Y-%m-%d")
            
            # 전략 분석
            signal = strategy.analyze(chart, i)
            
            # 매매 실행
            trade_log = self._execute_trade(ticker, portfolio, candle, signal, date_str)
            if trade_log:
                trade_logs.append(trade_log)
            
            # 일별 자산 평가 및 MDD 계산
            total_equity = self._evaluate_portfolio(portfolio, ticker, candle.close_price)
            daily_equity_curve[date_str] = float(total_equity.amount)
            self._update_mdd(total_equity.amount, mdd_tracker)

        # 4. 결과 생성
        return self._create_result(
            ticker, initial_capital, daily_equity_curve, 
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
        
        Returns:
            TradeLog or None: 거래가 실행되면 로그 반환, 아니면 None
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
        """
        매수 수량 계산
        
        Args:
            portfolio: 포트폴리오
            price: 매수 가격
            signal_quantity: 신호에서 지정한 수량 (None이면 최대 매수)
            
        Returns:
            Decimal: 매수 수량
        """
        if signal_quantity is not None:
            return signal_quantity
        
        # 거래 비용을 고려한 최대 매수 수량
        # total_cost = price * quantity * (1 + 0.003)
        # quantity = cash / (price * 1.003)
        total_rate = Decimal(1) + self.TRANSACTION_COST_RATE
        return Decimal(int(portfolio.cash.amount / (price.amount * total_rate)))
    
    def _calculate_sell_quantity(
        self, 
        position_quantity: Decimal, 
        signal_quantity: Optional[Decimal]
    ) -> Decimal:
        """
        매도 수량 계산
        
        Args:
            position_quantity: 보유 수량
            signal_quantity: 신호에서 지정한 수량 (None이면 전량 매도)
            
        Returns:
            Decimal: 매도 수량
        """
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
        ticker: Ticker, 
        current_price: Money
    ) -> Money:
        """
        포트폴리오 자산 평가
        
        Returns:
            Money: 총 자산 (현금 + 주식 평가액)
        """
        current_prices = {ticker.code: current_price}
        return portfolio.get_total_equity(current_prices)
    
    def _update_mdd(self, current_equity: Decimal, mdd_tracker: Dict[str, Decimal]) -> None:
        """
        MDD(Maximum Drawdown) 업데이트
        
        Args:
            current_equity: 현재 자산
            mdd_tracker: MDD 추적 딕셔너리 (peak, max_drawdown)
        """
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
        """
        백테스트 결과 객체 생성
        
        Returns:
            BacktestResult: 백테스트 결과
        """
        final_equity = Money.krw(list(daily_equity_curve.values())[-1]) if daily_equity_curve else initial_capital
        total_return = float((final_equity.amount - initial_capital.amount) / initial_capital.amount)
        
        return BacktestResult(
            ticker=ticker,
            total_return=total_return,
            final_equity=final_equity,
            initial_capital=initial_capital,
            mdd=float(max_drawdown) * -1,  # MDD는 음수로 표현
            trade_logs=trade_logs,
            daily_equity_curve=daily_equity_curve
        )

