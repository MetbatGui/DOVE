from src.domain.strategy.portfolio_strategy import PortfolioStrategy
from src.domain.strategy.presets.always_buy_evaluator import AlwaysBuyEvaluator

class BuyAndHoldStrategy(PortfolioStrategy):
    """
    한 번 매수하고 계속 보유하는 전략.
    실제 구현은 '매일 매수 시도'를 의미하지만, 잔고가 없으면 매수가 실행되지 않으므로
    결과적으로 Buy & Hold와 유사하게 동작합니다.
    """
    def __init__(self):
        # 기본 평가기로 AlwaysBuyEvaluator 사용
        super().__init__(evaluator=AlwaysBuyEvaluator())
