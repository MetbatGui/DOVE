import pytest
from src.domain.market.ticker import Ticker


def test_create_valid_ticker():
    ticker = Ticker(code="069500", name="KODEX 200")
    assert ticker.code == "069500"
    assert ticker.name == "KODEX 200"


def test_ticker_equality():
    """같은 code면 동일한 Ticker로 간주"""
    t1 = Ticker(code="069500", name="KODEX 200")
    t2 = Ticker(code="069500", name="Same Code")
    t3 = Ticker(code="123456", name="Other")

    assert t1 == t2
    assert t1 != t3


def test_invalid_ticker_code_length():
    """KRX 코드는 6자리여야 함"""
    with pytest.raises(ValueError):
        Ticker(code="06950", name="Short")

    with pytest.raises(ValueError):
        Ticker(code="0695000", name="Long")


def test_invalid_ticker_code_chars():
    """KRX 코드는 숫자로만 구성되어야 함"""
    with pytest.raises(ValueError):
        Ticker(code="A69500", name="Char")


def test_ticker_immutability():
    """Ticker는 불변 객체여야 함"""
    ticker = Ticker(code="069500", name="Old Name")
    with pytest.raises(ValueError, match="frozen"):
        ticker.code = "123456"
