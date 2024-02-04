from dataclasses import dataclass
from db.utils import to_unix_time
from db.sports import SPORT


@dataclass(frozen=True)
class Odd:
    name: str
    price: float


@dataclass
class Market:
    name: str
    odds: list[Odd]


@dataclass(frozen=True)
class Buk:
    name: str
    url : str


@dataclass
class PrematchEvent:
    name: str
    sport: SPORT
    buk: Buk
    country: str
    competition: str
    date: int | str
    open_market_count: int
    markets: list[Market]

    def __post_init__(self):
        self.date = to_unix_time(self.date)


@dataclass
class LiveEvent(PrematchEvent):
    score: str | None

    def __post_init__(self):
        super().__post_init__()
        self.name = self.name.replace('(live)', '').strip()


Event = PrematchEvent | LiveEvent
