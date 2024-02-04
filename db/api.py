import logging
from models import Event, PrematchEvent, LiveEvent

import apsw

from db.crud import (
    sport,
    event,
    event_group,
    event_group_fts5,
    buk,
    event_market,
    odd,
    market,
)
from db.sports import SPORT


logger = logging.getLogger(__name__)


def save_event(cur, ev: Event, event_group_id: int) -> None:
    is_live = False
    if isinstance(ev, LiveEvent):
        is_live = True

    logger.debug('TRY save event with name=%s', ev.name)

    buk_id = buk.insert(cur, ev.buk.name, ev.buk.url)
    event_id = event.upsert(
        cur,
        ev.name,
        ev.competition,
        ev.country,
        event_group_id,
        buk_id,
        ev.score,
        is_live,
        ev.open_market_count,
    )

    market_names = [market_data.name for market_data in ev.markets]
    market_ids = []
    for market_name in market_names:
        market_id = market.insert(cur, market_name)
        market_ids.append(market_id)

    event_market_ids = []
    for market_id in market_ids:
        event_market_id = event_market.insert(cur, event_id, market_id)
        event_market_ids.append(event_market_id)

    odd_ids = []
    for event_market_id, market_data in zip(event_market_ids, ev.markets):
        for odd_data in market_data.odds:
            odd_id = odd.upsert(cur, event_market_id, odd_data.name, odd_data.price)
            odd_ids.append(odd_id)

    logger.debug('SUCCESS save event with id=%d and name=%s', event_id, ev.name)
    return event_id


def save_event_groups_with_events(cur, event_groups):
    for event_group_key, group_events in event_groups.items():
        save_event_group_with_events(cur, event_group_key, group_events)


def save_event_group_with_events(cur, event_group_key: tuple[SPORT, int, str], group_events: list[Event]):
    sport_enum, date, event_name = event_group_key
    sport_name = sport_enum if isinstance(sport_enum, str) else sport_enum.value
    sport_id = sport.insert(cur, sport_name)
    event_group_id = save_event_group(cur, event_name, sport_id, date)

    for event_ in group_events:
        save_event(cur, event_, event_group_id)
        

def save_event_group(cur, event_group_name: str, sport_id: int, date: int) -> int:
    event_group_id = event_group.insert(cur, event_group_name, sport_id, date)
    res = event_group_fts5.insert(cur, event_group_name, sport_id, date)
    return event_group_id


def save_event_group_fts5(cur, event_group_name: str, sport_id: int, date: int):
    res = event_group_fts5.insert(cur, event_group_name, sport_id, date)
    


def delete_all_events(con: apsw.Connection) -> None:
    con.execute('DELETE FROM odd')
    con.execute('DELETE FROM event_market')
    con.execute('DELETE FROM event')
    