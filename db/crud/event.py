import logging
import apsw

from ..utils import to_score
from db.sports import SPORT, SPORTS


INSERT_EVENT_SQL = '''
INSERT INTO event(name, competition, country, event_group_id, buk_id, score, is_live, open_market_count)
VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
'''

UPSERT_EVENT_SQL = '''
INSERT INTO event(name, competition, country, event_group_id, buk_id, score, is_live, open_market_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(name, competition, country, event_group_id, buk_id) DO UPDATE SET
    score=excluded.score,
    is_live=excluded.is_live,
    open_market_count=excluded.open_market_count
RETURNING id
'''

SELECT_EVENT_ID_SQL = '''
SELECT id FROM event
WHERE event.name={event_name} AND
WHERE event.competition={competition} AND
WHERE event.country={country} AND
WHERE event.event_group_id={event_group_id} AND
WHERE event.buk_id={buk_id}
'''

DELETE_EVENT_SQL = 'DELETE FROM event WHERE event_id="{event_id}"'


logger = logging.getLogger(__name__)


def insert(
    cur,
    event_name: str,
    competition: str,
    country: str,
    event_group_id: int,
    buk_id: int,
    score: tuple[str, ...],
    is_live: bool,
    open_market_count: int,
) -> int | None:
    event_id = None
    event_tuple = (
        event_name,
        competition,
        country,
        event_group_id,
        buk_id,
        to_score(score),
        is_live,
        open_market_count,
    )
    try:
        logger.debug('TRY insert event with data=%r', event_tuple)
        res = cur.execute(INSERT_EVENT_SQL, event_tuple)
    except apsw.ConstraintError:
        event_id = select_id(cur, *event_tuple[:6])
        logger.debug('no need to insert event with data=%r, already exists', event_tuple)
    else:
        event_id = res.fetchone()[0]
        logger.debug('SUCCESS insert event with id=%d', event_id)
    return event_id


def upsert(
    cur,
    event_name: str,
    competition: str,
    country: str,
    event_group_id: int,
    buk_id: int,
    score: tuple[str, ...],
    is_live: bool,
    open_market_count: int,
) -> int | None:
    event_id = None
    event_tuple = (
        event_name,
        competition,
        country,
        event_group_id,
        buk_id,
        to_score(score),
        is_live,
        open_market_count
    )
    logger.debug('TRY upsert event with data=%r', event_tuple)
    res = cur.execute(UPSERT_EVENT_SQL, event_tuple)
    event_id = res.fetchone()[0]
    logger.debug('SUCCESS upsert event with id=%d', event_id)
    return event_id


def select_id(
    cur,
    event_name: str,
    competition: str,
    country: str,
    event_group_id: int,
    buk_id: int,
) -> int | None:
    query = SELECT_EVENT_ID_SQL.format(
        event_name=event_name,
        competition=competition,
        country=country,
        event_group_id=event_group_id,
        buk_id=buk_id,
    )
    logger.debug('TRY select event with name=%s', event_name)
    res = cur.execute(query)
    event_id = res.fetchone()[0]
    logger.debug('SUCCESS select event with name=%s and id=%d', event_name, event_id)
    return event_id


def delete(cur, event_id: int):
    logger.debug('TRY delete event with id=%d', event_id)
    res = cur.execute(DELETE_EVENT_SQL.format(event_id=event_id))
    event_id = res.fetchone()[0]
    logger.debug('SUCCESS upsert event with id=%d', event_id)
    return event_id
