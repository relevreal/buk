import logging
import apsw

INSERT_SPORT_SQL = 'INSERT INTO sport(name) VALUES(?) RETURNING id'
INSERT_OR_IGNORE_SPORT_SQL = 'INSERT OR IGNORE INTO sport(name) VALUES(?) RETURNING id'
SELECT_SPORT_ID_SQL = 'SELECT id FROM sport WHERE sport.name=\'{sport_name}\''


logger = logging.getLogger(__name__)

# use caching?
def insert(cur, sport_name: str):
    sport_id = None
    try:
        logger.debug('TRY insert sport: %s', sport_name)
        res = cur.execute(INSERT_SPORT_SQL, (sport_name,))
    except apsw.ConstraintError:
        sport_id = select_id(cur, sport_name)
        logger.debug('no need to insert sport: %s with id=%d, already exists', sport_name, sport_id)
    else:
        sport_id = res.fetchone()[0]
        logger.debug('SUCCES insert sport: %s with id=%d', sport_name, sport_id)
    return sport_id

    
def select_id(cur, sport_name: str):
    logger.debug('TRY select sport: %s', sport_name)
    res = cur.execute(SELECT_SPORT_ID_SQL.format(sport_name=sport_name))
    sport_id = res.fetchone()[0]
    logger.debug('SUCCESS select sport: %s with id=%d', sport_name, sport_id)
    return sport_id

