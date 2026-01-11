from src.domain.strategy.portfolio_strategy import PortfolioStrategy
from src.domain.strategy.presets.bollinger_band_evaluator import BollingerBandEvaluator

class BollingerBandStrategy(PortfolioStrategy):
    """
    볼린저 밴드 평균 회귀 전략.
    단일 자산 또는 다중 자산에 대해 BollingerBandEvaluator를 적용합니다.
    """
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        evaluator = BollingerBandEvaluator(period=period, multiplier=multiplier)
        super().__init__(evaluator=evaluator)
