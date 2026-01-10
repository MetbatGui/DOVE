import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import mplfinance as mpf
from pykrx import stock

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle
from src.domain.market.candle_chart import CandleChart
from src.domain.shared.money import Money
from src.domain.technical.moving_average import MovingAverage
from src.domain.technical.rsi import RSI
from src.domain.technical.macd import MACD

def main():
    # 1. 데이터 수집
    ticker_code = "005930"
    ticker_name = "Samsung Electronics" # 영문 이름 사용 (폰트 이슈 최소화)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=150)).strftime("%Y%m%d")
    
    print(f"[{ticker_name}({ticker_code})] Fetching data... ({start_date} ~ {end_date})")
    df = stock.get_market_ohlcv(start_date, end_date, ticker_code)
    
    # mplfinance 요구 컬럼명으로 변경
    df.rename(columns={
        '시가': 'Open', '고가': 'High', '저가': 'Low', 
        '종가': 'Close', '거래량': 'Volume'
    }, inplace=True)
    
    # 2. 도메인 객체로 변환하여 지표 계산 (로직 검증용)
    chart = CandleChart(ticker=Ticker(code=ticker_code, name=ticker_name), unit=CandleUnit.day())
    
    for date, row in df.iterrows():
        candle = Candle(
            open_price=Money.krw(row['Open']),
            high_price=Money.krw(row['High']),
            low_price=Money.krw(row['Low']),
            close_price=Money.krw(row['Close']),
            volume=int(row['Volume']),
            timestamp=date
        )
        chart.add_candle(candle)

    # 3. 지표 계산
    print("Calculating indicators...")
    
    # MA
    # Money.amount는 Decimal이므로 float로 변환 필요
    # None은 float('nan')으로 변환하여 mplfinance가 처리하도록 함
    ma5 = [float(v.amount) if v else float('nan') for v in MovingAverage(period=5).calculate(chart)]
    ma20 = [float(v.amount) if v else float('nan') for v in MovingAverage(period=20).calculate(chart)]
    ma60 = [float(v.amount) if v else float('nan') for v in MovingAverage(period=60).calculate(chart)]
    
    # RSI (이미 float or None)
    rsi = [v if v is not None else float('nan') for v in RSI(period=14).calculate(chart)]
    
    # MACD
    macd_res = MACD(fast_period=12, slow_period=26, signal_period=9).calculate(chart)
    macd = [float(r['macd']) if r['macd'] is not None else float('nan') for r in macd_res]
    signal = [float(r['signal']) if r['signal'] is not None else float('nan') for r in macd_res]
    hist = [float(r['histogram']) if r['histogram'] is not None else 0.0 for r in macd_res]

    # 4. 시각화 (mplfinance)
    # 추가 플롯 (AddPlots) 정의
    add_plots = [
        # MA (Panel 0: Price Overlay)
        mpf.make_addplot(ma5, panel=0, color='green', width=1, label='MA5'),
        mpf.make_addplot(ma20, panel=0, color='red', width=1, label='MA20'),
        mpf.make_addplot(ma60, panel=0, color='orange', width=1, label='MA60'),
        
        # RSI (Panel 2) - Panel 1 is Volume (handled by volume=True)
        mpf.make_addplot(rsi, panel=2, color='purple', ylabel='RSI(14)', ylim=(0, 100)),
        
        # MACD (Panel 3)
        mpf.make_addplot(macd, panel=3, color='black', width=1, ylabel='MACD'),
        mpf.make_addplot(signal, panel=3, color='red', width=1),
        mpf.make_addplot(hist, panel=3, type='bar', color=['r' if h>0 else 'b' for h in hist], alpha=0.5),
    ]

    # 라인 설정
    # RSI 70/30 라인은 make_addplot으로는 어려우므로, 리스트로 만들어서 추가하거나
    # mpf.plot의 hlines 등의 옵션을 사용할 수 있지만, 간단히 fill_between을 흉내내거나
    # 단순히 데이터를 추가하는게 편함. 여기선 간단히 70/30 시리즈를 추가.
    line_70 = [70] * len(df)
    line_30 = [30] * len(df)
    add_plots.append(mpf.make_addplot(line_70, panel=2, color='red', linestyle='--', width=0.5))
    add_plots.append(mpf.make_addplot(line_30, panel=2, color='blue', linestyle='--', width=0.5))

    # 스타일 설정 (한국형: 상승=Red, 하락=Blue)
    mc = mpf.make_marketcolors(
        up='red', 
        down='blue', 
        edge='inherit', 
        wick='inherit', 
        volume='inherit'
    )
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)

    # 스타일 및 저장
    save_file = 'samsung_mplfinance.png'
    print(f"Drawing chart to {save_file}...")
    
    # panel_ratios: Price=3, Volume=1, RSI=1, MACD=1
    mpf.plot(
        df,
        type='candle',
        style=s,
        volume=True,
        addplot=add_plots,
        panel_ratios=(3, 1, 1, 1),
        title=f"{ticker_name} ({ticker_code})",
        figsize=(15, 14),
        savefig=dict(fname=save_file, dpi=100, bbox_inches='tight')
    )
    print("Done!")

if __name__ == "__main__":
    main()
