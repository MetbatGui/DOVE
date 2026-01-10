from typing import List, Optional, Union, Iterator
from pydantic import BaseModel, PrivateAttr
from bisect import insort
from datetime import timedelta
from src.domain.market.ticker import Ticker
from src.domain.market.candle_unit import CandleUnit
from src.domain.market.candle import Candle

class CandleChart(BaseModel):
    """
    특정 종목(Ticker)과 시간 단위(CandleUnit)를 가지는 캔들 차트(컨테이너)입니다.
    캔들은 항상 시간순으로 정렬되어 유지됩니다.
    Pydantic을 사용하여 데이터 검증.
    """
    ticker: Ticker
    unit: CandleUnit
    _candles: List[Candle] = PrivateAttr(default_factory=list)

    model_config = {
        "frozen": False,
    }

    def __init__(self, ticker: Ticker, unit: CandleUnit, candles: Optional[List[Candle]] = None):
        super().__init__(ticker=ticker, unit=unit)
        if candles:
            for candle in candles:
                self.add_candle(candle)

    def add_candle(self, candle: Candle) -> None:
        """
        차트에 캔들을 추가합니다.
        이미 존재하는 시간의 캔들이라면 ValueERRor를 발생시킵니다.
        """
        # 중복 검사 (성능을 위해 마지막 캔들과 비교하거나 전체 검색 필요, 일단 간단히 구현)
        for c in self._candles:
            if c.timestamp == candle.timestamp:
                raise ValueError(f"Candle with timestamp {candle.timestamp} already exists")

        # 시간순 정렬 유지하며 삽입
        self._candles.append(candle)
        self._candles.sort(key=lambda x: x.timestamp)

    @property
    def candles(self) -> List[Candle]:
        """외부에서는 읽기 전용으로 접근"""
        return list(self._candles)

    def get_latest_candle(self) -> Optional[Candle]:
        """가장 최근(마지막) 캔들을 반환합니다."""
        if not self._candles:
            return None
        return self._candles[-1]

    def __len__(self) -> int:
        return len(self._candles)

    def verify(self) -> List[str]:
        """
        차트 데이터의 무결성을 검증합니다.
        
        Returns:
            발견된 문제점들의 리스트 (비어있으면 정상)
        """
        messages = []
        if not self._candles:
            messages.append("Chart is empty")
            return messages

        unit_delta = self.unit.to_timedelta()
        # Gap 허용 오차: 기본 단위의 3배 + 주말(2일) 고려
        # 예: 일봉이면 (1일*3 + 2일) = 5일 이상 차이나면 Gap으로 간주
        # 분봉이면 (5분*3) = 15분 이상 차이나면 Gap으로 간주
        gap_threshold = unit_delta * 3 + timedelta(days=2)

        for i in range(len(self._candles) - 1):
            curr = self._candles[i]
            next_c = self._candles[i+1]

            # 1. 정렬 및 중복 검사
            if curr.timestamp >= next_c.timestamp:
                messages.append(f"[Order/Duplicate] Index {i}: {curr.timestamp} >= {next_c.timestamp}")
                continue

            # 2. Gap 분석 (연속성)
            # 단순히 시간 차이가 너무 크면 알림
            time_diff = next_c.timestamp - curr.timestamp
            if time_diff > gap_threshold:
                 messages.append(f"[Gap] Index {i} -> {i+1}: Missing data between {curr.timestamp} and {next_c.timestamp} (Diff: {time_diff})")

        return messages
