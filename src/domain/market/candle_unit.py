from dataclasses import dataclass
from enum import Enum, auto

class UnitType(Enum):
    MINUTE = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()

@dataclass(frozen=True)
class CandleUnit:
    """
    캔들의 시간 단위를 나타내는 Value Object입니다.
    예: 1분, 5분, 1일, 1주 등
    """
    unit_type: UnitType
    value: int = 1

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Candle unit value must be positive")

    @classmethod
    def minute(cls, value: int = 1) -> 'CandleUnit':
        return cls(UnitType.MINUTE, value)

    @classmethod
    def day(cls, value: int = 1) -> 'CandleUnit':
        return cls(UnitType.DAY, value)

    @classmethod
    def week(cls, value: int = 1) -> 'CandleUnit':
        return cls(UnitType.WEEK, value)

    @classmethod
    def month(cls, value: int = 1) -> 'CandleUnit':
        return cls(UnitType.MONTH, value)

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
