import asyncio
import logging
import httpx
from datetime import datetime
from pprint import pprint

from utils import timer
from db.sports import SPORT
from models import PrematchEvent, LiveEvent, Buk, Market, Odd


logger = logging.getLogger(__name__)


BUK_NAME = 'betfan'
BUK_URL = 'https://betfan.pl'
LIVE_URL = 'https://api-v2.betfan.pl/api/v1/livebetting/running/events?getGameTypeCodes=true'
ALL_CATEGORIES_URL = 'https://api-v2.betfan.pl/api/v1/market/categories/all'
CATEGORIES_WITH_BETS_URL = 'https://api-v2.betfan.pl/api/v1/market/categories?date=&hours='
CATEGORY_EVENTS_URL = 'https://api-v2.betfan.pl/api/v1/market/categories/{category_id}/events?date=&hours='


BUK = Buk(name=BUK_NAME, url=BUK_URL)


SPORT_MAP = {
    'Badminton': SPORT.BADMINTON,
    'Baseball': SPORT.BASEBALL,
    'CS2/CS:GO': SPORT.COUNTER_STRIKE,
    'Darts': SPORT.DARTS,
    'Dota': SPORT.DOTA_2,
    'ESport': SPORT.ESPORT,
    'Futsal': SPORT.FUTSAL,
    'Hokej': SPORT.ICE_HOCKEY,
    'Koszykówka': SPORT.BASKETBALL,
    'LoL': SPORT.LEAGUE_OF_LEGENDS,
    'Piłka nożna': SPORT.FOOTBALL,
    'Piłka ręczna': SPORT.HANDBALL,
    'Piłka wodna': SPORT.WATERBALL,
    'Rugby': SPORT.RUGBY,
    'Siatkówka': SPORT.VOLLEYBALL,
    'Siatkówka plażowa': SPORT.BEACH_VOLLEYBALL,
    'Snooker': SPORT.SNOOKER,
    'Tenis': SPORT.TENNIS,
    'Tenis stołowy': SPORT.TABLE_TENNIS,
}


@timer
async def get_betfan_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get prematch events')
    resp = await c.get(CATEGORIES_WITH_BETS_URL)

    if resp.status_code != 200:
        return []

    categories = resp.json()['data']['categories']
    events = []
    for category in categories:
        logger.debug('TRY get %d events for %s category', category['eventsCount'], category['categoryName'])
        if category['eventsCount'] >= 500:
            for subcategory in category['children']:
                resp = await c.get(CATEGORY_EVENTS_URL.format(category_id=subcategory['categoryId']))
                if resp.status_code != 200:
                    await asyncio.sleep(5)
                    continue
                subcategory_events_data = resp.json()
                subcategory_events = _get_category_prematch_events(subcategory_events_data)
                events += subcategory_events
                resp = await c.get(CATEGORY_EVENTS_URL.format(category_id=subcategory['categoryId']))
                logger.debug('SUCCESS got %d events for %s subcategory', len(subcategory_events), subcategory['categoryName'])
                await asyncio.sleep(5)
            continue

        resp = await c.get(CATEGORY_EVENTS_URL.format(category_id=category['categoryId']))

        if resp.status_code != 200:
            asyncio.sleep(1)
            continue

        category_events_data = resp.json()
        category_events = _get_category_prematch_events(category_events_data)
        events += category_events
        logger.debug('SUCCESS got %d events for %s category', len(category_events), category['categoryName'])
        await asyncio.sleep(5)
    logger.info('SUCCESS got %d prematch events', len(events))
    return events


@timer
async def get_betfan_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get live events')
    try:
        resp = await c.get(LIVE_URL)
    except httpx.HTTPError as exc:
        logger.error('Error while getting live events', exc_info=exc)
        return []

    if resp.status_code != 200:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []

    events = []
    data = resp.json()['data'] 
    sports_data = data['sports']

    for sport_data in sports_data:
        logger.debug('TRY get events for sport: %s', sport_data['sportName'])
        game_types_data = sport_data['gameTypes']

        markets_dict = {}
        for gt_data in game_types_data.values():
            for game_data in gt_data:
                event_id = game_data['eventId']
                odds = []
                for odd in game_data['outcomes']:
                    name = odd.get('outcomeName', None)
                    price = odd.get('outcomeOdds', None)
                    if name is None or price is None:
                        break
                    odd = Odd(name, price)
                    odds.append(odd)
                else:
                    continue

                market = Market(
                    name=game_data['gameName'],
                    odds=odds,
                )
                if event_id in markets_dict:
                    markets_dict[event_id].append(market)
                else:
                    markets_dict[event_id] = [market]

        sport_name = sport_data['sportName']
        sport = SPORT_MAP.get(sport_name, None)
        if sport is None:
            logger.info('skipping %d sport events, unknown sport: \'%s\'', len(sport_data), sport_name)
            continue

        sport_events_num = 0
        for event_data in sport_data['events']:
            if event_data['isLive']:
                event_id = event_data['eventId']
                event = LiveEvent(
                    name=event_data['eventName'],
                    sport=sport,
                    score=event_data['score'],
                    date=event_data['eventStart'],
                    buk=BUK,
                    competition=event_data['categoryName'],
                    country=event_data['parentName'],
                    open_market_count=1,
                    markets=markets_dict.get(event_id, []),
                )
                events.append(event)
                sport_events_num += 1
        logger.debug('SUCCESS got %s events for sport: %s', sport_events_num, sport_data['sportName'])
    logger.info('SUCCESS got %d live events', len(events))
    return events


########################
### HELPER FUNCTIONS ###
########################


def _get_category_prematch_events(category_events_data: dict[str, any]) -> list[PrematchEvent]:
    subcategories = category_events_data['data']['categories']
    events = []
    for subcategory in subcategories:
        for event_data in subcategory['events']:
            event = PrematchEvent(
                name=event_data['eventName'],
                date=event_data['eventStart'],
                sport=event_data['sportName'],
                buk=BUK,
                competition=event_data['categoryName'],
                country=event_data['parentName'],
                open_market_count=event_data['gamesCount'],
                markets=_get_markets(event_data['games']),
            )
            events.append(event)
    return events


def _get_markets(markets_data: dict[str, any]) -> list[Market]:
    markets = []
    for market_data in markets_data:
        market = Market(
            name=market_data['gameName'],
            odds=[
                Odd(name=odd['outcomeName'], price=odd['outcomeOdds'])
                for odd in market_data['outcomes']
            ]
        )
        markets.append(market)
    return markets