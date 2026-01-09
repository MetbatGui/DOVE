from dataclasses import dataclass

@dataclass(frozen=True)
class Ticker:
    """
    시장(Market)에서 거래되는 종목의 고유 식별자(Identifier)입니다.
    Value Object로서 불변성(Immutable)을 가지며, 한국 시장(KRX) 표준인 6자리 코드를 검증합니다.
    """
    code: str
    name: str

    def __post_init__(self):
        # KRX 종목 코드 검증: 6자리 숫자
        if not (len(self.code) == 6 and self.code.isdigit()):
            raise ValueError(f"Invalid KRX ticker code: {self.code}")

    def __str__(self) -> str:
        return f"{self.name}({self.code})"

    def __eq__(self, other):
        if not isinstance(other, Ticker):
            return False
        return self.code == other.code
