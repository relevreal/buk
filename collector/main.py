import asyncio
import logging
import traceback
import time
import httpx
from pprint import pprint

import apsw
from Levenshtein import distance

from db.sports import SPORT
from db.api import save_event, delete_all_events, save_event_groups_with_events
from create_db import create_db
from .buks.api import (
    get_betclic_prematch,
    get_betclic_live,
    get_betcris_prematch_ws,
    get_betcris_live_ws,
    get_betfan_prematch,
    get_betfan_live,
    get_betters_prematch_ws,
    get_betters_live_ws,
    get_comeon_live_ws,
    get_ebetx_prematch,
    get_ebetx_live,
    get_efortuna_prematch,
    get_efortuna_live,
    get_etoto_prematch,
    get_etoto_live,
    get_goplusbet_prematch_ws,
    get_goplusbet_live_ws,
    get_lvbet_prematch,
    get_lvbet_live,
    get_pzbuk_live_ws,
    get_sts_prematch,
    get_sts_live,
    get_superbet_prematch,
    get_superbet_live,
    get_totalbet_prematch,
    get_totalbet_live,
    get_iforbet_prematch,
    get_iforbet_live,
    get_fuksiarz_prematch,
    get_fuksiarz_live,
)


logger = logging.getLogger(__name__)


# No longer accept bets 
# BETWAY_URL = None

# Only horses
# TRAF_URL = None

# No longer accepts bets
# TOTOLOTEK_URL = None

# Website doesn't work
# LVBET24_URL = None

# Website doesn't work
# FUNBETS_URL = None

# Website doesn't work
# WETTARENA_URL = None


def catch_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.critical(traceback.format_exc())
    return wrapper


def get_buk_live_tasks(c: httpx.AsyncClient): 
    return [
        get_betclic_live(c),
        get_betfan_live(c),
        # get_efortuna_live(c), ???
        get_etoto_live(c),
        get_sts_live(c),
        # get_ebetx_live(c),
        # get_lvbet_live(c),
        # get_superbet_live(c),
        # get_totalbet_live(c), 
        # get_iforbet_live(c),
        # get_fuksiarz_live(c),

        # get_pzbuk_live_ws(c), 
        # get_comeon_live_ws(c), 
        # get_betcris_live_ws(),
        # get_goplusbet_live_ws(),
        # get_betters_live_ws(),
    ]
        # http_funcs = [
        #     get_betclic_live,
        #     get_betfan_live,
        #     # get_efortuna_live(c), ???
        #     get_etoto_live,
        #     get_sts_live,
        #     get_ebetx_live,
        #     get_lvbet_live,
        #     get_superbet_live,
        #     get_totalbet_live, 
        #     get_iforbet_live,
        #     get_fuksiarz_live,
        # ]
        # http_tasks = [catch_error(http_func)(c) for http_func in http_funcs]
        # ws_funcs = [
        #     # get_pzbuk_live_ws, 
        #     # get_comeon_live_ws, 
        #     # get_betcris_live_ws,
        #     # get_goplusbet_live_ws,
        #     # get_betters_live_ws,
        # ] 
        # ws_tasks = [catch_error(ws_func)() for ws_func in ws_funcs]
        # return http_tasks + ws_tasks
 

async def collect_live(db_path: str, wait_for: int, fresh_db: bool = False):
        if fresh_db:
            create_db(db_path)
        con = apsw.Connection(db_path)
        async with httpx.AsyncClient() as c:
            while True:
                try:
                    start = time.time()
                    delete_all_events(con)
                    delete_end = time.time()
                    live_tasks = get_buk_live_tasks(c)
                    results = await asyncio.gather(*live_tasks)
                    
                    # TODO map every sport to common name
                    # TODO groups together all same events
                    # key: (name, sport, datetime)?
                    # value: list[Event]
                    event_groups = {}
                    event_group_buks = {}
                    sport_time_groups = {}
                    # with con:
                    for result in results:
                        for event in result:
                            sport_time_key = (event.sport, event.date)
                            event_names: list[str] | None = sport_time_groups.get(sport_time_key, None)
                            if event_names is None:
                                sport_time_groups[sport_time_key] = [event.name]
                                event_key = (sport_time_key[0], sport_time_key[1], event.name)
                                event_groups[event_key] = [event]
                                event_group_buks[event_key] = {event.buk}
                            else:
                                for event_name in event_names:
                                    is_sim = is_similar(event_name, event.name)
                                    event_key = (sport_time_key[0], sport_time_key[1], event_name)
                                    group_buks = event_group_buks.get(event_key, None)
                                    if group_buks is None:
                                        group_buks = set()
                                        event_group_buks[event_key] = group_buks

                                    if is_sim and event.buk not in group_buks:
                                        group_buks.add(event.buk)
                                        event_groups[event_key].append(event)
                                        break
                                    continue
                                else:
                                    sport_time_groups[sport_time_key].append(event.name)
                                    event_key = (sport_time_key[0], sport_time_key[1], event.name)
                                    event_groups[event_key] = [event]
                                    event_group_buks[event_key] = {event.buk}
                                            
                                # save_event(con, event)
                                
                    # gs = [(k, v) for k, v in event_groups.items() if len(v) > 1]
                    # gns = [(k, v) for k, v in event_groups.items() if len(v) == 1]
                    # pprint(groups)
                    # print(sorted(set(event.sport if isinstance(event.sport, str) else event.sport.value for result in results for event in result)))
                    # exit(1)

                    with con:
                        save_event_groups_with_events(con, event_groups)

                    end = time.time()
                    elapsed = end - start
                    delete_elapsed = delete_end - start
                    wait_for_left = wait_for - elapsed
                    print(f'deleted elapsed: {delete_elapsed:.5f}')
                    print(f'elapsed: {elapsed:.3f}s, wait for: {wait_for_left:.3f}s')
                    await asyncio.sleep(wait_for - elapsed)
                except Exception as e:
                    logging.critical('error in collect live function while loop')
                    logging.critical(traceback.format_exc())
                    await asyncio.sleep(20)


def _processor(s: str) -> str:
    sorted_words = sorted(w.lower().strip() for w in s.split(' '))
    processed = ''.join(
        c 
        for w in sorted_words 
        for c in w
        if c.isalnum()
    )
    return processed

# (insertion, deletion, substitution)
WEIGHTS = (2, 5, 5)

def calculate_distance(s1: str, s2: str) -> int:
    if len(s2) < len(s1):
        s1, s2 = s2, s1
    return distance(s1, s2, weights=WEIGHTS, processor=_processor)
    

BORDER = 50.0


def is_similar(s1: str, s2: str) -> bool:
    dist = calculate_distance(s1, s2)
    value = weight(dist, s1, s2)
    if value <= BORDER:
        return True
    return False


def weight(dist: float, s1: str, s2: str):
    s1_len = len(s1)
    s2_len = len(s2)
    smaller, larger = (s1_len, s2_len) if s1_len < s2_len else (s2_len, s1_len)
    ratio = smaller / (larger + 10) + 1
    value = dist * ratio
    return value


async def main():
    async with httpx.AsyncClient() as c:
        # data = await get_betclic_prematch(c)
        # data = await get_betclic_live(c)

        # data = await get_betfan_prematch(c)
        # data = await get_betfan_live(c)

        # data = await get_efortuna_prematch(c)
        data = await get_efortuna_live(c)

        # data = await get_etoto_prematch(c)
        # data = await get_etoto_live(c)

        # data = await get_sts_prematch(c)
        # data = await get_sts_live(c)

        # data = await get_ebetx_prematch(c)
        # data = await get_ebetx_live(c)

        # data = await get_superbet_prematch(c)
        # data = await get_superbet_live(c)

        # data = await get_lvbet_prematch(c)
        # data = await get_lvbet_live(c)

        # data = await get_totalbet_prematch(c)
        # data = await get_totalbet_live(c)

        # data = await get_iforbet_prematch(c)
        # data = await get_iforbet_live(c)

        # data = await get_fuksiarz_prematch(c)
        # data = await get_fuksiarz_live(c)

        # data = await get_betcris_prematch_ws()
        # data = await get_betcris_live_ws()

        # data = await get_goplusbet_prematch_ws()
        # data = await get_goplusbet_live_ws()

        # data = await get_betters_prematch_ws()
        # data = await get_betters_live_ws()

        # data = await get_betters_prematch_ws()
        # data = await get_pzbuk_live_ws(c)
        
    pprint(data[0])
    print(len(data))


if __name__ == '__main__':
    # asyncio.run(main())
    asyncio.run(collect_live(20))
    