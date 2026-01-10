from datetime import date
from decimal import Decimal
from typing import List

from src.domain.market.ticker import Ticker
from src.domain.shared.money import Money
from src.domain.portfolio.portfolio import Portfolio
from src.domain.strategy.strategy import Strategy
from src.domain.strategy.trading_signal import SignalType
from src.ports.market_data_provider import MarketDataProvider
from src.application.dto.backtest_result import BacktestResult, TradeLog

class BacktestService:
    """
    백테스트 시뮬레이션을 수행하는 애플리케이션 서비스.
    """
    def __init__(self, data_provider: MarketDataProvider):
        self.data_provider = data_provider

    def run(self, ticker: Ticker, strategy: Strategy, start_date: date, end_date: date, initial_capital: Money) -> BacktestResult:
        # 1. 데이터 준비
        chart = self.data_provider.get_ohlcv(ticker, start_date, end_date)
        if not chart.candles:
            raise ValueError("No data found for the given range.")

        # 2. 포트폴리오 초기화 (현금 포함, 거래 비용 자동 처리)
        portfolio = Portfolio(initial_capital)
        
        trade_logs: List[TradeLog] = []
        daily_equity_curve = {}
        
        mdd_peak = initial_capital.amount
        max_drawdown = Decimal(0)

        # 3. 시뮬레이션 루프
        for i, candle in enumerate(chart.candles):
            date_str = candle.timestamp.strftime("%Y-%m-%d")
            current_price = candle.close_price  # 종가 기준 매매
            
            # 전략 분석
            signal = strategy.analyze(chart, i)
            
            # 매매 실행 로직 (거래 비용은 Portfolio가 자동 처리)
            if signal.type == SignalType.BUY:
                if portfolio.cash.amount > 0:
                    quantity_to_buy = signal.quantity
                    
                    if quantity_to_buy is None:
                        # 거래 비용을 고려하여 최대 매수 수량 계산
                        # total_cost = price * quantity * (1 + 0.003)
                        # quantity = cash / (price * 1.003)
                        total_rate = Decimal(1) + Decimal("0.003")  # commission + slippage
                        quantity_to_buy = Decimal(int(portfolio.cash.amount / (current_price.amount * total_rate)))
                    
                    if quantity_to_buy > 0:
                        try:
                            # Portfolio.buy가 알아서 현금 확인 및 거래 비용 처리
                            portfolio.buy(ticker, quantity_to_buy, current_price)
                            
                            # 거래 비용 포함된 실제 차감 금액 계산 (로그용)
                            stock_cost = current_price * quantity_to_buy
                            transaction_fee = stock_cost * Decimal("0.003")
                            total_cost = stock_cost + Money(transaction_fee.amount, current_price.currency)
                            
                            trade_logs.append(TradeLog(
                                date=date_str,
                                action="BUY",
                                quantity=quantity_to_buy,
                                price=current_price,
                                amount=total_cost,
                                reason=signal.reason
                            ))
                        except ValueError:
                            # 현금 부족 등으로 매수 실패 (무시)
                            pass

            elif signal.type == SignalType.SELL:
                position = portfolio.get_position(ticker)
                if position:
                    quantity_to_sell = signal.quantity
                    if quantity_to_sell is None:
                        quantity_to_sell = position.quantity
                    
                    if quantity_to_sell > position.quantity:
                        quantity_to_sell = position.quantity

                    if quantity_to_sell > 0:
                        try:
                            # Portfolio.sell이 알아서 거래 비용 처리
                            portfolio.sell(ticker, current_price, quantity_to_sell)
                            
                            # 거래 비용 차감된 실제 수령 금액 계산 (로그용)
                            gross_revenue = current_price * quantity_to_sell
                            transaction_fee = gross_revenue * Decimal("0.003")
                            net_revenue = gross_revenue - Money(transaction_fee.amount, current_price.currency)
                            
                            trade_logs.append(TradeLog(
                                date=date_str,
                                action="SELL",
                                quantity=quantity_to_sell,
                                price=current_price,
                                amount=net_revenue,
                                reason=signal.reason
                            ))
                        except ValueError:
                            # 수량 부족 등으로 매도 실패 (무시)
                            pass

            # 일별 자산 평가 (Portfolio가 자동 계산)
            current_prices = {ticker.code: current_price}
            total_equity = portfolio.get_total_equity(current_prices)
            daily_equity_curve[date_str] = float(total_equity.amount)
            
            # MDD 계산
            if total_equity.amount > mdd_peak:
                mdd_peak = total_equity.amount
            
            drawdown = (mdd_peak - total_equity.amount) / mdd_peak if mdd_peak > 0 else Decimal(0)
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 4. 결과 생성
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
