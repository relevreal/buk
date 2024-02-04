EVENT_TABLE_NAME = 'event'

CREATE_EVENT_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS event(
    id                  INTEGER     PRIMARY KEY,
    name                TEXT        NOT NULL,
    competition         TEXT        NOT NULL,
    country             TEXT,
    event_group_id      INTEGER     NOT NULL,
    buk_id              INTEGER     NOT NULL,
    score               TEXT,
    is_live             INTEGER     NOT NULL,
    open_market_count   INTEGER NOT NULL,

    UNIQUE(name, competition, country, event_group_id, buk_id),

    FOREIGN KEY(event_group_id) REFERENCES event_group(id),
    FOREIGN KEY(buk_id) REFERENCES buk(id)
)
'''

DROP_EVENT_TABLE_SQL = 'DROP TABLE IF EXISTS event'
