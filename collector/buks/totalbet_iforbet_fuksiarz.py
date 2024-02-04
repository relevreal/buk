import asyncio
import logging
import httpx
from operator import itemgetter
from pprint import pprint

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


logger = logging.getLogger(__name__)


TOTALBET_BUK_NAME = 'totalbet'
TOTALBET_BUK_URL = 'https://www.totalbet.pl'
TOTALBET_BUK = Buk(TOTALBET_BUK_NAME, TOTALBET_BUK_URL)

IFORBET_BUK_NAME = 'iforbet'
IFORBET_BUK_URL = 'https://www.iforbet.pl'
IFORBET_BUK = Buk(IFORBET_BUK_NAME, IFORBET_BUK_URL)

FUKSIARZ_BUK_NAME = 'fuksiarz'
FUKSIARZ_BUK_URL = 'https://www.fuksiarz.pl'
FUKSIARZ_BUK = Buk(FUKSIARZ_BUK_NAME, FUKSIARZ_BUK_URL)

buk_dict = {
    TOTALBET_BUK_NAME: TOTALBET_BUK,
    IFORBET_BUK_NAME: IFORBET_BUK,
    FUKSIARZ_BUK_NAME: FUKSIARZ_BUK,
}

TOTALBET_CATEGORIES_URL = 'https://totalbet.pl/rest/market/categories'
TOTALBET_CATEGORY_EVENTS_URL = 'https://totalbet.pl/rest/market/categories/multi/{category_id}/events'
TOTALBET_LIVE_URL = 'https://totalbet.pl/livebetting-api/rest/livebetting/v1/api/running/games/major?nocache=1704716827955'

IFORBET_CATEGORIES_URL = 'https://www.iforbet.pl/rest/market/categories'
IFORBET_CATEGORY_EVENTS_URL = 'https://www.iforbet.pl/rest/market/categories/multi/{category_id}/events'
IFORBET_LIVE_URL = 'https://www.iforbet.pl/livebetting-api/rest/livebetting/v1/api/running/games/major'

FUKSIARZ_CATEGORIES_URL = 'https://fuksiarz.pl/rest/market/categories'
FUKSIARZ_CATEGORY_EVENTS_URL = 'https://fuksiarz.pl/rest/market/categories/multi/{category_id}/events'
FUKSIARZ_LIVE_URL = 'https://fuksiarz.pl/livebetting-api/rest/livebetting/v1/api/running/games/major?nocache=1704714801335'


@timer
async def get_totalbet_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    return await _get_prematch_events(c, 'totalbet', TOTALBET_CATEGORIES_URL, TOTALBET_CATEGORY_EVENTS_URL)


@timer
async def get_totalbet_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    return await _get_live_events(c, 'totalbet', TOTALBET_LIVE_URL)


@timer
async def get_iforbet_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    return await _get_prematch_events(c, 'iforbet', IFORBET_CATEGORIES_URL, IFORBET_CATEGORY_EVENTS_URL)


@timer
async def get_iforbet_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    return await _get_live_events(c, 'iforbet', IFORBET_LIVE_URL)


@timer
async def get_fuksiarz_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    return await _get_prematch_events(c, 'fuksiarz', FUKSIARZ_CATEGORIES_URL, FUKSIARZ_CATEGORY_EVENTS_URL)


@timer
async def get_fuksiarz_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    return await _get_live_events(c, 'fuksiarz', FUKSIARZ_LIVE_URL)


#############
### UTILS ###
#############


async def _get_prematch_events(c: httpx.AsyncClient, buk_name: str, categories_url: str, category_events_url: str) -> list[PrematchEvent]:
    logger.info('TRY get %s prematch events', buk_name)
    resp = await c.get(categories_url)
    
    if resp.status_code != 200:
        logger.info('skipping %s prematch events, got response status code: %d', buk_name, resp.status_code)
        return []
    
    categories_data = resp.json()['data']
    seen_categories = set()
    events = []
    for i, category_data in enumerate(sorted(categories_data, key=itemgetter('level', 'categoryId'))):
        category_id = category_data['categoryId']
        parent_category_id = category_data['parentCategory']
        level = category_data['level']
        already_seen = (
            category_id in seen_categories or (
                level > 1 and parent_category_id in seen_categories
            )
        )
        seen_categories.add(category_id)

        logger.debug('TRY get %s prematch events for category: %s and level: %d [%d/%d]', buk_name, category_data['categoryName'], level, i, len(category_data))

        if already_seen:
            continue

        resp = await c.get(category_events_url.format(category_id=category_id))

        if resp.status_code != 200:
            logger.info('skipping %s prematch events, got response status code: %d when getting category: %d', buk_name, resp.status_code, category_data['categoryName'])
            continue

        events_data = resp.json()['data']
        for event_data in events_data:
            event = PrematchEvent(
                name=event_data['eventName'],
                buk=buk_dict[buk_name],
                date=event_data['eventStart'],
                sport=event_data['category1Name'],
                competition=event_data['category2Name'],
                country=event_data['category3Name'],
                open_market_count=event_data['gamesCount'],
                markets=_get_markets(event_data['eventGames']),
            )
            events.append(event)

        await asyncio.sleep(3) 
    
    logger.info('SUCCESS got %d %s prematch events', len(events), buk_name)
    return events


async def _get_live_events(c: httpx.AsyncClient, buk_name: str, live_url: str) -> list[LiveEvent]:
    logger.info('TRY get %s live events', buk_name)
    resp = await c.get(live_url)

    if resp.status_code != 200:
        logger.info('skipping %s live events, got response status code: %d', buk_name, resp.status_code)
        return []

    events_data = resp.json()
    events = _get_events(events_data, buk_name)

    # pprint(events[-1])

    logger.info('SUCCESS got %d %s live events', len(events), buk_name)
    return events


def _get_events(events_data, buk_name: str) -> list[LiveEvent]:
    events = []
    for event_data in events_data['data']:
        if 'games' in event_data:
            event = LiveEvent(
                name=event_data['eventName'],
                buk=buk_dict[buk_name],
                sport=event_data['sportName'],
                date=event_data['eventStart'],
                country=event_data['categoryName'],
                competition=event_data['parentName'],
                score=event_data['score'],
                open_market_count=event_data['gamesCount'],
                markets=_get_markets(event_data['games']),
            )
            events.append(event)
    return events
    

def _get_markets(markets_data: dict[str, any]) -> list[Market]:
    markets = []
    for market_data in markets_data:
        odds = []
        for o in market_data['outcomes']:
            name = o.get('outcomeName', None)
            price = o.get('outcomeOdds', None)
            if name is None or price is None:
                break
            odd = Odd(name, price)
            odds.append(odd)
        else:
            continue

        market = Market(
            name=market_data['gameName'],
            odds=odds,
        )
        markets.append(market)
    return markets
