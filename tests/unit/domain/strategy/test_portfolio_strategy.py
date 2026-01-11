from unittest.mock import MagicMock
from datetime import date
from src.domain.strategy.trading_signal import TradingSignal, SignalType
from src.domain.strategy.portfolio_strategy import PortfolioStrategy

# PortfolioStrategy가 의존하는 클래스들을 Mocking하거나 가볍게 사용
# TradingSignal은 DTO이므로 실제 객체 사용 (데이터 전달용)

def test_portfolio_strategy_analysis_flow():
    """
    PortfolioStrategy가:
    1. Universe의 각 차트에서 날짜 인덱스를 찾고
    2. 데이터가 있으면 Evaluator를 호출하고
    3. 결과 Signal을 수집하는지 검증
    (외부 의존성 없이 Mock만 사용)
    """
    # Arrange
    mock_evaluator = MagicMock()
    
    # 두 개의 종목에 대한 Mock Chart 준비
    mock_chart_a = MagicMock()
    mock_chart_a.find_index_by_date.return_value = 10  # 10번째 날짜에 데이터 있음
    
    mock_chart_b = MagicMock()
    mock_chart_b.find_index_by_date.return_value = -1  # 데이터 없음 (휴장일 등)
    
    universe = {
        "TICKER_A": mock_chart_a,
        "TICKER_B": mock_chart_b
    }
    
    # Chart에 Ticker 설정 (Strategy가 주입할 때 사용)
    mock_ticker_a = MagicMock()
    mock_chart_a.ticker = mock_ticker_a
    
    # Evaluator 동작 정의
    expected_base_signal = TradingSignal(type=SignalType.BUY, reason="Test Buy")
    mock_evaluator.evaluate.return_value = expected_base_signal
    
    # System Under Test
    strategy = PortfolioStrategy(evaluator=mock_evaluator)
    target_date = date(2025, 1, 1)
    
    # Act
    results = strategy.analyze(universe, target_date)
    
    # Assert
    # 1. Chart A는 데이터가 있으므로 Evaluator가 호출되어야 함
    mock_chart_a.find_index_by_date.assert_called_with(target_date)
    mock_evaluator.evaluate.assert_called_with(mock_chart_a, 10)
    
    # 2. 결과에는 A의 시그널만 있어야 함
    assert len(results) == 1
    assert "TICKER_A" in results
    
    result_signal = results["TICKER_A"]
    # Ticker가 주입되었는지 확인
    assert result_signal.ticker == mock_ticker_a
    # 나머지 정보는 Evaluator가 반환한 것과 같아야 함
    assert result_signal.type == expected_base_signal.type
    assert result_signal.reason == expected_base_signal.reason
