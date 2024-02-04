import logging
import apsw

INSERT_ODD_SQL = 'INSERT INTO odd(event_market_id, name, price) VALUES (?, ?, ?) RETURNING id'

UPSERT_ODD_SQL = '''
INSERT INTO odd(event_market_id, name, price) VALUES (?, ?, ?)
ON CONFLICT(event_market_id, name) DO UPDATE SET
    price=excluded.price
RETURNING id
'''

SELECT_ODD_SQL = '''
SELECT id FROM odd
WHERE odd.event_market_id={event_market_id} AND
WHERE odd.name={odd_name}
'''


logger = logging.getLogger(__name__)


def insert(cur, event_market_id: int, name: str, price: float) -> int | None:
    odd_id = None
    try:
        logger.debug('TRY insert odd with event_market_id=%d, name=%s, price=%f', event_market_id, name, price)
        res = cur.execute(INSERT_ODD_SQL, (event_market_id, name, price))
    except apsw.ConstraintError:
        odd_id = select_id(cur, event_market_id, name)
        logger.debug('no need to insert odd with event_market_id=%d, name=%s, price=%f, already exists', event_market_id, name, price)
    else:
        odd_id = res.fetchone()[0]
        logger.debug('SUCCES insert odd with event_market_id=%d, name=%s, price=%f', event_market_id, name, price)
    return odd_id


def upsert(cur, event_market_id: int, name: str, price: float) -> int | None:
    logger.debug('TRY upsert odd with event_market_id=%d, name=%s, price=%f', event_market_id, name, price)
    res = cur.execute(UPSERT_ODD_SQL, (event_market_id, name, price))
    odd_id = res.fetchone()[0]
    logger.debug('SUCCES upsert odd with id=%d', odd_id)
    return odd_id


def select_id(cur, event_market_id: int, name: str) -> int | None:
    logger.debug('TRY select odd with event_market_id=%d and name=%s', event_market_id, name)
    query = SELECT_ODD_SQL.format(
        event_market_id=event_market_id,
        name=name,
    )
    res = cur.execute(query)
    odd_id = res.fetchone()[0]
    logger.debug('SUCCESS select odd with id=%d', odd_id)
    return odd_id
