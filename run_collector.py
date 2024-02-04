import httpx
import asyncio

import apsw

from collector.main import main, collect_live


if __name__ == '__main__':
    from logger import init_logger
    init_logger()

    # asyncio.run(main())
    asyncio.run(collect_live(db_path='buks.db', wait_for=20, fresh_db=True))
