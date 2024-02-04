import logging
import apsw

INSERT_MARKET_SQL = 'INSERT INTO market(name) VALUES (?) RETURNING id'
SELECT_MARKET_SQL = 'SELECT id FROM market WHERE market.name=?'


logger = logging.getLogger(__name__)


def insert(cur, market_name: str) -> int | None:
    market_id = None
    try:
        logger.debug('TRY insert market: %s', market_name)
        res = cur.execute(INSERT_MARKET_SQL, (market_name,))
    except apsw.ConstraintError:
        market_id = select_id(cur, market_name)
        logger.debug('no need to insert market: %s with id=%d, already exists', market_name, market_id)
    else:
        market_id = res.fetchone()[0]
        logger.debug('SUCCES insert market: %s with id=%d', market_name, market_id)
    return market_id 


def select_id(cur, market_name: str) -> int | None:
    logger.debug('TRY select market: %s', market_name)
    res = cur.execute(SELECT_MARKET_SQL, (market_name,))
    market_id = res.fetchone()[0]
    logger.debug('SUCCESS select market: %s with id=%d', market_name, market_id)
    return market_id
