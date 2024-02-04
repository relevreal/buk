import asyncio
import logging
import httpx
from pprint import pprint

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import (
    batched,
    timer,
)


logger = logging.getLogger(__name__)


BUK_NAME = 'lvbet'
BUK_URL = 'https://lvbet.pl/pl/'
BUK = Buk(BUK_NAME, BUK_URL)

PREMATCH_URL = 'https://offer.lvbet.pl/client-api/v4/matches/?is_pre=true&lang=pl'
PRIMARY_MARKET_URL = 'https://offer.lvbet.pl/client-api/v4/matches/primary-column-markets/?lang=pl&matches_ids={match_ids}'
SPORT_GROUPS_URL = 'https://offer.lvbet.pl/client-api/v4/sports-groups/?country=pl&lang=pl&sports_groups_ids={sport_group_ids}'
ALL_MARKETS_URL = 'https://offer.lvbet.pl/client-api/v4/markets/search/?lang=pl&hide_unavailable=false&matches_ids={match_ids}'

LIVE_URL = 'https://offer.lvbet.pl/client-api/v4/matches/?lang=pl&is_live=true'
LIVE_MATCH_STATISTICS = 'https://offer.lvbet.pl/client-api/v4/matches/statistics/?lang=pl&matches_ids={match_ids}'


@timer
async def get_lvbet_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get lvbet prematch events')
    try:
        resp = await c.get(PREMATCH_URL)
    except httpx.HTTPError:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []

    if resp.status_code != 200:
        logger.error('skipping prematch events, got response status code: %d', resp.status_code)
        return []
    
    events_json = resp.json()
    events_data = []
    sport_group_ids = set() 
    match_ids = []
    for event_data in events_json:
        match_id = event_data['match_id']
        home = event_data['home'][0]
        if event_data['away'] is None:
            name = home
        else:
            away = event_data['away'][0]
            name = f'{home} - {away}'

        event = {
            'match_id': event_data['match_id'],
            'name': name,
            'sport_group_ids': event_data['sports_groups_ids'],
            'date': event_data['date'],
            'open_market_count': event_data['state']['markets_count'],
        }

        sport_group_ids.update(str(sgi) for sgi in event_data['sports_groups_ids'])
        match_ids.append(str(match_id))

        events_data.append(event)

    sport_group_ids_str = ','.join(sport_group_ids)
    resp = await c.get(SPORT_GROUPS_URL.format(sport_group_ids=sport_group_ids_str))

    if resp.status_code != 200:
        logger.info('skipping lvbet prematch events, got response status code: %d when getting sport groups', resp.status_code)
        return []

    sport_groups_data = resp.json()

    sport_groups_dict = {
        sgd['sports_group_id']: sgd['name']
        for sgd in sport_groups_data
    }

    markets_dict = {}
    for i, batched_match_ids in enumerate(batched(match_ids, 10)):
        resp = await c.get(PRIMARY_MARKET_URL.format(match_ids=','.join(batched_match_ids)))
        
        if resp.status_code != 200:
            logger.info('skipping lvbet prematch events, got response status code: %d when getting primary markets', resp.status_code)
            continue

        markets_data = resp.json()
        for market_data in markets_data:
            market = {
                'name': market_data['name'],
                'odds': [
                    (odd['name'], odd['rate']['decimal'])
                    for odd in market_data['selections']
                ],
            }
            match_id = market_data['match_id']
            if match_id not in markets_dict:
                markets_dict[match_id] = [market]
            else:
                markets_dict[match_id].append(market)

        logger.debug('creating markets dict: %d/%d', i, len(match_ids) // 10)
        
        await asyncio.sleep(3)
        
    events = []
    for event_data in events_data:
        sport_groups = [
            sport_groups_dict[sgi] 
            for sgi in event['sport_group_ids']
        ]

        match_id = event['match_id']
        if match_id not in markets_dict:
            markets = []
        else:
            markets = markets_dict[match_id]

        event = PrematchEvent(
            name=event_data['name'],
            buk=BUK,
            sport=sport_groups[0],
            competition=sport_groups[1],
            country=sport_groups[2],
            date=_get_date(event_data['date']),
            open_market_count=event_data['open_market_count'],
            markets=markets,
        )
        events.append(event)
    
    logger.info('SUCCESS got %d lvbet prematch events', len(events))
    return events



@timer
async def get_lvbet_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get lvbet prematch events')
    try:
        resp = await c.get(LIVE_URL)
    except httpx.HTTPError as exc:
        logger.error('Error while getting lvbet live events', exc_info=exc)
        return []

    if resp.status_code != 200:
        logger.error('skipping lvbet live events, got response status code: %d', resp.status_code)
        return []
    
    events_json = resp.json()
    events_data = []
    sport_group_ids = []
    match_ids = []
    for event_data in events_json:
        match_id = event_data['match_id']
        home = event_data['home'][0]
        if event_data['away'] is None:
            name = home
        else:
            away = event_data['away'][0]
            name = f'{home} - {away}'

        event = {
            'match_id': event_data['match_id'],
            'name': name,
            'sport_group_ids': event_data['sports_groups_ids'],
            'date': event_data['date'],
            'open_market_count': event_data['state']['markets_count'],
        }

        sport_group_ids.extend(str(sgi) for sgi in event_data['sports_groups_ids'])
        match_ids.append(str(match_id))

        events_data.append(event)

    market_tasks = [
        c.get(PRIMARY_MARKET_URL.format(match_ids=','.join(batched_match_ids)))
        for batched_match_ids in batched(match_ids, 10)
    ]

    sport_group_ids_str = ','.join(sport_group_ids)
    sport_groups_task = c.get(SPORT_GROUPS_URL.format(sport_group_ids=sport_group_ids_str))

    all_match_ids = ','.join(match_ids)
    match_statistics_task = c.get(LIVE_MATCH_STATISTICS.format(match_ids=all_match_ids))

    try:
        results = await asyncio.gather(*market_tasks, sport_groups_task, match_statistics_task)
    except httpx.HTTPError as exc:
        logger.error('Error while getting lvbet live market, sport groups, and match statistics tasks', exc_info=exc)
        return []

    if any(result.status_code != 200 for result in results):
        logger.info('skipping lvbet live events, got response status code: %d when trying to get sport groups', resp.status_code)
        return []
        
    match_statistics_data = results.pop().json()
    score_dict = {
        ms['match_id']: tuple(ms['total_score'].values())
        for ms in match_statistics_data
    }

    sport_groups_data = results.pop().json()
    sport_groups_dict = {
        sgd['sports_group_id']: sgd['name']
        for sgd in sport_groups_data
    }
        
    markets_dict: dict[str, Market] = {}
    for market_data_result in results:
        markets_data = market_data_result.json() 
        for market_data in markets_data:
            market = Market(
                name=market_data['name'],
                odds=[
                    Odd(name=odd['name'], price=odd['rate']['decimal'])
                    for odd in market_data['selections']
                ],
            )
            match_id = market_data['match_id']
            if match_id not in markets_dict:
                markets_dict[match_id] = [market]
            else:
                markets_dict[match_id].append(market)

    events = []
    for event_data in events_data:
        match_id = event_data['match_id']
        if match_id not in markets_dict:
            markets = []
        else:
            markets = markets_dict[match_id]

        sport_groups = [
            sport_groups_dict[sgi] 
            for sgi in event_data['sport_group_ids']
        ]

        score = score_dict.get(match_id, None)

        event = LiveEvent(
            name=event_data['name'],
            buk=BUK,
            score=score,
            sport=sport_groups[0],
            competition=sport_groups[1],
            country=sport_groups[2],
            date=_get_date(event_data['date']),
            open_market_count=event_data['open_market_count'],
            markets=markets,
        )
        events.append(event)
    
    logger.info('SUCCESS got %d lvbet live events', len(events))
    # pprint(events[-1])
    return events


def _get_date(date_str: str) -> str:
    return date_str.split('+')[0] + 'Z'
