ODD_TABLE_NAME = 'odd'

CREATE_ODD_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS odd(
    id INTEGER PRIMARY KEY,
    event_market_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,

    UNIQUE(event_market_id, name),

    FOREIGN KEY(event_market_id) REFERENCES event_market(id)
)
'''

DROP_ODD_TABLE_SQL = 'DROP TABLE IF EXISTS odd'
