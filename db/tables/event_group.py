EVENT_GROUP_TABLE_NAME = 'event_group'

CREATE_EVENT_GROUP_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS event_group(
    id                  INTEGER     PRIMARY KEY,
    name                TEXT        NOT NULL,
    sport_id            INTEGER     NOT NULL,
    date                INTEGER     NOT NULL,

    UNIQUE(name, sport_id, date),

    FOREIGN KEY(sport_id) REFERENCES sport(id)
)
'''

DROP_EVENT_GROUP_TABLE_SQL = 'DROP TABLE IF EXISTS event_group'
