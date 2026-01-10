from pydantic import BaseModel, field_validator

class Ticker(BaseModel):
    """
    종목을 식별하는 값 객체 (Value Object).
    Pydantic을 사용하여 자동 타입 검증 지원.
    KRX 표준 6자리 코드 검증 포함.
    """
    code: str
    name: str

    model_config = {
        "frozen": True,  # 불변성 유지
    }

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """KRX 종목 코드 검증: 6자리 숫자"""
        if not (len(v) == 6 and v.isdigit()):
            raise ValueError(f"Invalid KRX ticker code: {v}")
        return v

    def __hash__(self) -> int:
        """Pydantic BaseModel은 기본적으로 해시 불가능하므로 명시적 구현"""
        return hash((self.code, self.name))

    def __str__(self) -> str:
        return f"{self.name}({self.code})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Ticker):
            return False
        return self.code == other.code
