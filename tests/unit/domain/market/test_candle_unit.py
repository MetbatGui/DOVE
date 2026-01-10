import pytest
from src.domain.market.candle_unit import CandleUnit, UnitType

class TestCandleUnit:
    def test_create_basic_units(self):
        """기본적인 캔들 단위 생성 테스트"""
        u = CandleUnit.minute(5)
        assert u.unit_type == UnitType.MINUTE
        assert u.value == 5

        u = CandleUnit.day()
        assert u.unit_type == UnitType.DAY
        assert u.value == 1

    def test_validation(self):
        """유효하지 않은 값 검증 테스트"""
        with pytest.raises(ValueError, match="positive"):
            CandleUnit.minute(0)
        
        with pytest.raises(ValueError, match="positive"):
            CandleUnit.minute(-5)

    def test_equality(self):
        """동등성 비교 테스트 (Value Object 특성)"""
        u1 = CandleUnit.minute(5)
        u2 = CandleUnit.minute(5)
        u3 = CandleUnit.minute(10)
        u4 = CandleUnit.day(1)

        assert u1 == u2
        assert u1 != u3
        assert u1 != u4

    def test_string_representation(self):
        """문자열 표현 테스트"""
        assert str(CandleUnit.minute(1)) == "1분"
        assert str(CandleUnit.minute(5)) == "5분"
        assert str(CandleUnit.day(1)) == "일봉"
        assert str(CandleUnit.day(3)) == "3일"
        assert str(CandleUnit.week(1)) == "주봉"
        assert str(CandleUnit.month(1)) == "월봉"
