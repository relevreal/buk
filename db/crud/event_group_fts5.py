import logging
import apsw

INSERT_EVENT_GROUP_FTS5_SQL = 'INSERT INTO event_group_fts5(name, sport_id, date) VALUES (?, ?, ?)'
SELECT_EVENT_GROUP_FTS5_SQL = 'SELECT * FROM event_group_fts5(? + ? + ?) ORDER BY rank'


logger = logging.getLogger(__name__)


def insert(cur, event_group_name: str, sport_id: int, date: int) -> int | None:
    event_group_id = None
    logger.debug('TRY insert: %s', event_group_name)
    res = cur.execute(INSERT_EVENT_GROUP_FTS5_SQL, (event_group_name, sport_id, date))
    event_group_id = res.fetchone()[0]
    logger.debug('SUCCES insert: %s with id: %d', event_group_name, event_group_id)
    return event_group_id


def select_matching(cur, event_group_name: str, sport_id: int, date: int):
    logger.debug('TRY select: %s', event_group_name)
    res = cur.execute(SELECT_EVENT_GROUP_FTS5_SQL, (event_group_name, sport_id, date))
    event_groups = res.fetchall()
    logger.debug('SUCCESS select: found %d matching event groups', len(event_groups))
    return event_groups