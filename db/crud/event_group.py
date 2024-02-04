import logging
import apsw

INSERT_EVENT_GROUP_SQL = 'INSERT INTO event_group(name, sport_id, date) VALUES (?, ?, ?) RETURNING id'
SELECT_EVENT_GROUP_SQL = 'SELECT id FROM event_group WHERE event_group.name=?'

logger = logging.getLogger(__name__)


def insert(cur, event_group_name: str, sport_id: int, date: int) -> int | None:
    event_group_id = None
    try:
        logger.debug('TRY insert: %s', event_group_name)
        res = cur.execute(INSERT_EVENT_GROUP_SQL, (event_group_name, sport_id, date))
    except apsw.ConstraintError:
        event_group_id = select_id(cur, event_group_name)
        logger.debug('no need to insert: %s with id: %d, already exists', event_group_name, event_group_id)
    else:
        event_group_id = res.fetchone()[0]
        logger.debug('SUCCES insert: %s with id: %d', event_group_name, event_group_id)
    return event_group_id


def select_id(cur, event_group_name: str) -> int | None:
    logger.debug('TRY select: %s', event_group_name)
    res = cur.execute(SELECT_EVENT_GROUP_SQL, (event_group_name,))
    event_group_id = res.fetchone()[0]
    logger.debug('SUCCESS select event group: %s with id: %d', event_group_name, event_group_id)
    return event_group_id