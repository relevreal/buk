EVENT_MARKET_TABLE_NAME = 'event_market'

CREATE_EVENT_MARKET_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS event_market(
    id          INTEGER     PRIMARY KEY,
    event_id    INTEGER     NOT NULL,
    market_id   INTEGER     NOT NULL,
    
    UNIQUE(event_id, market_id),

    FOREIGN KEY(event_id) REFERENCES event(id),
    FOREIGN KEY(market_id) REFERENCES market(id)
)
'''

DROP_EVENT_MARKET_TABLE_SQL = 'DROP TABLE IF EXISTS event_market'
