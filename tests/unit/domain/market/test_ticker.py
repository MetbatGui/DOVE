import pytest
from src.domain.market.ticker import Ticker

def test_create_valid_ticker():
    """정상적인 Ticker 생성 테스트"""
    ticker = Ticker("069500", "KODEX 200")
    assert ticker.code == "069500"
    assert ticker.name == "KODEX 200"
    assert str(ticker) == "KODEX 200(069500)"

def test_ticker_equality():
    """Ticker 동등성 비교 테스트 (코드 기준)"""
    t1 = Ticker("069500", "KODEX 200")
    t2 = Ticker("069500", "Same Code")
    t3 = Ticker("123456", "Other")

    assert t1 == t2  # 코드가 같으면 같은 객체 취급
    assert t1 != t3

def test_invalid_ticker_code_length():
    """6자리가 아닌 경우 에러 발생"""
    with pytest.raises(ValueError, match="Invalid KRX ticker"):
        Ticker("06950", "Short")
        
    with pytest.raises(ValueError):
        Ticker("0695000", "Long")

def test_invalid_ticker_code_chars():
    """숫자가 아닌 문자가 포함된 경우 에러 발생"""
    with pytest.raises(ValueError):
        Ticker("A69500", "Char")

def test_ticker_immutability():
    """불변 객체 수정 시도 시 에러 발생"""
    ticker = Ticker("069500", "Old Name")
    with pytest.raises(AttributeError):
        ticker.code = "123456"
