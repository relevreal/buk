BUK_TABLE_NAME = 'buk'

CREATE_BUK_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS buk(
    id       INTEGER     PRIMARY KEY,
    name     TEXT        UNIQUE NOT NULL,
    url      TEXT        NOT NULL
)
'''.format(table_name=BUK_TABLE_NAME)

DROP_BUK_TABLE_SQL = 'DROP TABLE IF EXISTS buk'
