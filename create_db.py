from pprint import pprint
import logging

import click
import apsw
import apsw.bestpractice

apsw.bestpractice.apply(apsw.bestpractice.recommended)
apsw.ext.log_sqlite(level=logging.DEBUG)

# import sqlite3
# from utils import print_all_tables, timer
from utils import timer
# from db.api import save_event
# from event_generator import generate_events, Config
from db.tables import CREATE_TABLES_SQL, DROP_TABLES_SQL
from db.api import save_event
from event_generator import Config, generate_events


logger = logging.getLogger(__name__)


@timer
def create_db(db_path: str):
    con = apsw.Connection(db_path)
    with con:
        _drop_tables(con)
        _create_tables(con) 


# @click.command()
# @click.option('--drop/--no-drop', default=True)
@timer
def main():
    con = apsw.Connection('buks.db')
    with con:
        _drop_tables(con)
        _create_tables(con) 
        _insert_events(con)


def _drop_tables(con):
    logger.debug('TRY drop tables')
    for table_name, drop_table_sql in DROP_TABLES_SQL:
        con.execute(drop_table_sql)
        logger.debug('SUCCESS drop table: %s', table_name)
    logger.debug('SUCCES drop tables')


def _create_tables(con):
    logger.debug('TRY create tables')
    for table_name, create_table_sql in CREATE_TABLES_SQL:
        con.execute(create_table_sql)
        logger.debug('SUCCESS create table: %s', table_name)
    logger.debug('SUCCESS create tables')


# def _print_all_tables(con):
#     res = con.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')
#     all_tables = [r[0] for r in res.fetchall()]
#     pprint(all_tables)


def _insert_events(con):
    logger.debug('TRY insert: %d events into database', 100)
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
    for event in events:
        save_event(con, event)
    logger.debug('SUCCESS insert: %d events into database', 100)


if __name__ == '__main__':
    from logger import init_logger
    init_logger()

    main()