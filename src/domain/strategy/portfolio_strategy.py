from typing import Dict, List, Optional
from datetime import date
from src.domain.market.candle_chart import CandleChart
from src.domain.strategy.strategy import Strategy
from src.domain.strategy.trading_signal import TradingSignal, TradingSignal
from src.domain.strategy.asset_evaluator import AssetEvaluator

class PortfolioStrategy(Strategy):
    """
    여러 자산(Multi-Asset)을 동시에 분석하고 관리하는 포트폴리오 전략.
    Composite Strategy 패턴의 Composite 역할을 수행합니다.
    """
    
    def __init__(self, evaluator: AssetEvaluator):
        self.evaluator = evaluator

    def analyze(self, universe_data: Dict[str, CandleChart], current_date: date) -> Dict[str, TradingSignal]:
        """
        전체 유니버스를 순회하며 각 종목을 평가하고, 최종 포트폴리오 신호를 생성합니다.
        """
        universe_signals: Dict[str, TradingSignal] = {}
        
        # 1. 개별 종목 평가 (Bottom-up)
        for ticker_code, chart in universe_data.items():
            # 해당 날짜의 데이터가 있는지 확인
            idx = chart.find_index_by_date(current_date)
            if idx == -1:
                continue
                
            # 하위 평가기 실행
            signal = self.evaluator.evaluate(chart, idx)
            
            # 시그널에 티커 정보가 없다면 주입 (Evaluator가 안 채워줬을 경우 대비)
            if signal.ticker is None:
                # Pydantic 모델은 불변일 수 있으므로 copy & update 필요할 수 있음
                # 여기서는 frozen=True가 설정되어 있으므로 model_copy 사용
                signal = signal.model_copy(update={"ticker": chart.ticker})
                
            universe_signals[ticker_code] = signal
        
        # 2. 포트폴리오 레벨의 최종 판단
        return self._aggregate_signals(universe_signals)

    def _aggregate_signals(self, raw_signals: Dict[str, TradingSignal]) -> Dict[str, TradingSignal]:
        """
        개별 종목 신호들을 취합하여 최종 신호를 확정합니다.
        기본 구현은 모든 신호를 그대로 반환합니다.
        """
        return raw_signals
