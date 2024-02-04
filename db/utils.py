from datetime import datetime
import time
from pprint import pprint

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def to_unix_time(dt: int | str) -> int:
    if isinstance(dt, int):
        if dt <= 9_999_999:
            return dt
        return int(''.join(d for d in str(dt))[:10])
    dt = datetime.strptime(dt, DATE_FORMAT)
    return int(time.mktime(dt.timetuple()))


def from_unix_time(dt: int) -> str:
    return datetime.utcfromtimestamp(dt).strftime(DATE_FORMAT)


def date_to_str(dt: datetime):
    dt_str = datetime.strftime(dt, DATE_FORMAT)
    return dt_str


def to_score(score: str | None):
    if score is None:
        return None
    return ','.join(score)


def print_all_tables(cur):
    res = cur.execute('SELECT * FROM sport')
    pprint(res.fetchall())
    res = cur.execute('SELECT * FROM buk')
    pprint(res.fetchall())
    res = cur.execute('SELECT * FROM event')
    pprint(res.fetchall())
    res = cur.execute('SELECT * FROM market')
    pprint(res.fetchall())
    res = cur.execute('SELECT * FROM event_market')
    pprint(res.fetchall())
    res = cur.execute('SELECT * FROM odd')
    pprint(res.fetchall())
