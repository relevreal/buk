import logging
import apsw

INSERT_EVENT_MARKET_SQL = 'INSERT INTO event_market(event_id, market_id) VALUES (?, ?) RETURNING id'
SELECT_EVENT_MARKET_SQL = 'SELECT id FROM event_market WHERE event_id={event_id} AND market_id={market_id}'


logger = logging.getLogger(__name__)


def insert(cur, event_id: int, market_id: int) -> int | None:
    event_market_id = None
    try:
        logger.debug('TRY insert event market with event_id=%d and market_id=%d', event_id, market_id)
        res = cur.execute(INSERT_EVENT_MARKET_SQL, (event_id, market_id))
    except apsw.ConstraintError:
        event_market_id = select_id(cur, event_id, market_id)
        logger.debug('no need to insert event market with event_id=%d and market_id=%d, already exists', event_id, market_id)
    else:
        event_market_id = res.fetchone()[0]
        logger.debug('SUCCESS insert event market with event_id=%d and market_id=%d', event_id, market_id)
    return event_market_id


def select_id(cur, event_id: int, market_id: int) -> int | None:
    logger.debug('TRY select event market with event_id=%d and market_id=%d', event_id, market_id)
    query = SELECT_EVENT_MARKET_SQL.format(
        event_id=event_id,
        market_id=market_id,
    )
    res = cur.execute(query)
    event_market_id = res.fetchone()[0]
    logger.debug('SUCCES select event market with id=%d', event_market_id)
    return event_market_id
