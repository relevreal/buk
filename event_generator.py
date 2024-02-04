from dataclasses import dataclass
import random
import datetime as dt
from pprint import pprint

from db.utils import date_to_str
from models import Event, Market, Odd


@dataclass
class Config:
    n_events: int
    n_competitions: int
    n_countries: int
    n_bukies: int
    n_sports: int
    n_markets: int
    avg_markets_per_event: int
    avg_bukies_with_same_event: int


def generate_events(config: Config) -> list[Event]:
    avg_bukies_with_same_event = config.avg_bukies_with_same_event
    # (event_name, number_of_bukies_with_this_event)
    event_params = [
        (f'event_{i}', random.randint(1, avg_bukies_with_same_event + 1))
        for i in range(1, config.n_events+1)
    ]
    sports = [f'sport_{i}' for i in range(1, config.n_sports+1)]
    competitions = [f'competition_{i}' for i in range(1, config.n_competitions+1)] 
    countries = [f'country_{i}' for i in range(1, config.n_countries+1)] 
    bukies = [(f'buk_{i}', f'https://www.buk_{i}.pl') for i in range(1, config.n_bukies+1)] 
    markets = [
        Market(
            name=f'market_{i}',
            odds=[
                Odd(name='1', price=random.uniform(0.0, 50.0)),
                Odd(name='x', price=random.uniform(0.0, 50.0)),
                Odd(name='2', price=random.uniform(0.0, 50.0)),
            ],
        )
        for i in range(1, config.n_markets+1)
    ]

    events = []
    for event_name, n_events in event_params:
        event_date = dt.datetime.now() + dt.timedelta(minutes=random.randrange(300))
        event_bukies = random.sample(bukies, n_events)
        for buk_name in event_bukies:
            n_event_markets = random.randint(1, 2*config.avg_markets_per_event + 1)
            event_markets = random.sample(markets, n_event_markets)

            event = Event(
                name=event_name,
                sport=sports[random.randrange(len(sports))],
                buk=buk_name,
                country=countries[random.randrange(len(countries))],
                competition=competitions[random.randrange(len(competitions))],
                date=date_to_str(event_date),
                score=f'{random.randrange(5)},{random.randrange(5)}',
                open_market_count=random.randrange(100) + n_event_markets,
                is_live=True,
                markets=event_markets,
            )
            events.append(event)
    
    return events

    
if __name__ == '__main__':
    from create_db import save_event

    config = Config(
        n_events=200,
        n_competitions=20,
        n_countries=10,
        n_bukies=17,
        n_sports=20,
        n_markets=10,
        avg_markets_per_event=2,
        avg_bukies_with_same_event=11,
    )
    events = generate_events(config)
    print(len(events))