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

        # 2. 포트폴리오 초기화
        # 주의: 현재 Portfolio 클래스는 '현금'을 명시적으로 관리하지 않는 단순 버전임.
        # 따라서 여기서는 '가상의 현금'을 지역 변수로 관리하며 시뮬레이션함.
        # 추후 Portfolio가 Cash를 내장하도록 리팩토링할 필요성이 있음.
        portfolio = Portfolio()
        current_cash = initial_capital
        
        trade_logs: List[TradeLog] = []
        daily_equity_curve = {}
        
        mdd_peak = initial_capital.amount
        max_drawdown = Decimal(0)

        # 3. 시뮬레이션 루프
        for i, candle in enumerate(chart.candles):
            date_str = candle.timestamp.strftime("%Y-%m-%d")
            current_price = candle.close_price # 심플하게 종가 기준 매매 가정
            
            # 전략 분석
            signal = strategy.analyze(chart, i)
            
            # 매매 실행 로직
            if signal.type == SignalType.BUY:
                # 매수 가능 금액 확인 (일단 전액 매수 시도 or 수량 지정)
                # 시그널에 수량이 없으면 '가용 현금 범위 내 최대''로 가정
                 if current_cash.amount > 0:
                    quantity_to_buy = signal.quantity
                    
                    if quantity_to_buy is None:
                        # 수수료 고려 X, 단순 계산: 현금 / 주가
                        quantity_to_buy = Decimal(int(current_cash.amount / current_price.amount))
                    
                    if quantity_to_buy > 0:
                        cost = current_price * quantity_to_buy
                        if cost <= current_cash:
                            portfolio.buy(ticker, quantity_to_buy, current_price)
                            current_cash -= cost
                            
                            trade_logs.append(TradeLog(
                                date=date_str,
                                action="BUY",
                                quantity=quantity_to_buy,
                                price=current_price,
                                amount=cost,
                                reason=signal.reason
                            ))

            elif signal.type == SignalType.SELL:
                # 보유 수량 확인
                position = portfolio.get_position(ticker)
                if position:
                    quantity_to_sell = signal.quantity
                    # 수량 없으면 전량 매도
                    if quantity_to_sell is None:
                        quantity_to_sell = position.quantity
                    
                    # 보유량보다 많이 팔 수 없음
                    if quantity_to_sell > position.quantity:
                        quantity_to_sell = position.quantity

                    if quantity_to_sell > 0:
                        revenue = current_price * quantity_to_sell
                        portfolio.sell(ticker, quantity_to_sell)
                        current_cash += revenue
                        
                        trade_logs.append(TradeLog(
                            date=date_str,
                            action="SELL",
                            quantity=quantity_to_sell,
                            price=current_price,
                            amount=revenue,
                            reason=signal.reason
                        ))

            # 일별 자산 평가 (Equity = Cash + Stock Value)
            position_value = Money.krw(0)
            position = portfolio.get_position(ticker)
            if position:
                position_value = current_price * position.quantity
            
            total_equity = current_cash + position_value
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
            mdd=float(max_drawdown) * -1, # MDD는 음수로 표현
            trade_logs=trade_logs,
            daily_equity_curve=daily_equity_curve
        )
