import pytest
from decimal import Decimal
from src.domain.shared.money import Money, Currency

def test_create_money_krw():
    """KRW Money 객체 생성 테스트"""
    money = Money.krw(10000)
    assert money.amount == Decimal("10000")
    assert money.currency == Currency.KRW

def test_money_addition():
    """같은 통화 덧셈 테스트"""
    m1 = Money.krw(1000)
    m2 = Money.krw(2000)
    result = m1 + m2
    assert result.amount == Decimal("3000")
    assert result.currency == Currency.KRW

def test_money_subtraction():
    """같은 통화 뺄셈 테스트"""
    m1 = Money.krw(5000)
    m2 = Money.krw(1000)
    result = m1 - m2
    assert result.amount == Decimal("4000")

def test_money_multiplication():
    """곱셈 연산 테스트"""
    m1 = Money.krw(1000)
    result = m1 * 3
    assert result.amount == Decimal("3000")
    
    # float 곱셈도 지원 확인
    result_float = m1 * 2.5
    assert result_float.amount == Decimal("2500")

def test_money_format_str():
    """문자열 포맷팅 테스트"""
    m1 = Money.krw(1234567)
    assert str(m1) == "1,234,567원"

def test_money_comparison():
    """대소 타당성 비교 테스트"""
    m1 = Money.krw(1000)
    m2 = Money.krw(2000)
    m3 = Money.krw(1000)
    
    assert m1 < m2
    assert m2 > m1
    assert m1 == m3
    assert m1 <= m3

def test_different_currency_error():
    """다른 통화 연산 시 에러 발생 테스트"""
    krw = Money.krw(1000)
    usd = Money(Decimal("10"), Currency.USD)
    
    with pytest.raises(ValueError):
        krw + usd
        
    with pytest.raises(ValueError):
        krw - usd
        
    with pytest.raises(ValueError):
        krw < usd
