import logging
import apsw

INSERT_BUK_SQL = 'INSERT INTO buk(name, url) VALUES (?, ?) RETURNING id'
SELECT_BUK_SQL = 'SELECT id FROM buk WHERE buk.name=\'{buk_name}\''

logger = logging.getLogger(__name__)


def insert(cur, buk_name: str, buk_url: str) -> int | None:
    buk_id = None
    try:
        logger.debug('TRY insert buk: %s', buk_name)
        res = cur.execute(INSERT_BUK_SQL, (buk_name, buk_url))
    except apsw.ConstraintError:
        buk_id = select_id(cur, buk_name)
        logger.debug('no need to insert buk: %s with id: %d, already exists', buk_name, buk_id)
    else:
        buk_id = res.fetchone()[0]
        logger.debug('SUCCES insert buk: %s with id: %d', buk_name, buk_id)
    return buk_id


def select_id(cur, buk_name: str) -> int | None:
    logger.debug('TRY select buk: %s', buk_name)
    res = cur.execute(SELECT_BUK_SQL.format(buk_name=buk_name))
    buk_id = res.fetchone()[0]
    logger.debug('SUCCESS select buk: %s with id: %d', buk_name, buk_id)
    return buk_id