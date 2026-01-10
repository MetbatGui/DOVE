from pydantic import BaseModel, field_validator
from enum import Enum, auto

class UnitType(Enum):
    MINUTE = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()

from datetime import timedelta

class CandleUnit(BaseModel):
    """
    캔들의 시간 단위를 나타내는 Value Object입니다.
    예: 1분, 5분, 1일, 1주 등
    """
    unit_type: UnitType
    value: int = 1

    model_config = {
        "frozen": True,
    }

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Candle unit value must be positive")
        return v

    def to_timedelta(self) -> timedelta:
        """단위를 timedelta로 변환합니다."""
        if self.unit_type == UnitType.MINUTE:
            return timedelta(minutes=self.value)
        elif self.unit_type == UnitType.DAY:
            return timedelta(days=self.value)
        elif self.unit_type == UnitType.WEEK:
            return timedelta(weeks=self.value)
        elif self.unit_type == UnitType.MONTH:
            # 월 단위는 가변적이므로 근사치(30일) 사용 혹은 검증 시 주의 필요
            return timedelta(days=30 * self.value)
        return timedelta(0)

    @classmethod
    def minute(cls, value: int = 1) -> 'CandleUnit':
        return cls(unit_type=UnitType.MINUTE, value=value)

    @classmethod
    def day(cls, value: int = 1) -> 'CandleUnit':
        return cls(unit_type=UnitType.DAY, value=value)

    @classmethod
    def week(cls, value: int = 1) -> 'CandleUnit':
        return cls(unit_type=UnitType.WEEK, value=value)

    @classmethod
    def month(cls, value: int = 1) -> 'CandleUnit':
        return cls(unit_type=UnitType.MONTH, value=value)

    def __str__(self) -> str:
        if self.unit_type == UnitType.MINUTE:
            return f"{self.value}분"
        elif self.unit_type == UnitType.DAY:
            return f"{self.value}일" if self.value > 1 else "일봉"
        elif self.unit_type == UnitType.WEEK:
            return f"{self.value}주" if self.value > 1 else "주봉"
        elif self.unit_type == UnitType.MONTH:
            return f"{self.value}개월" if self.value > 1 else "월봉"
        return f"{self.value} {self.unit_type.name}"
