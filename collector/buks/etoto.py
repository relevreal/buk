import logging
import httpx
from operator import itemgetter
import asyncio
from pprint import pprint

from db.sports import SPORT
from models import PrematchEvent, LiveEvent, Buk, Market, Odd


BUK_NAME = 'etoto'
BUK_URL = 'https://www.etotot.py'
CATEGORIES_URL = 'https://api.etoto.pl/rest/market/categories'
CATEGORY_EVENTS_URL = 'https://api.etoto.pl/rest/market/categories/multi/{category_id}/events'
LIVE_URL = 'https://api.etoto.pl/livebetting-api/rest/livebetting/v1/api/running/games/major'


BUK = Buk(name=BUK_NAME, url=BUK_URL)


logger = logging.getLogger(__name__)


SPORT_MAP = {
    'Badminton': SPORT.BADMINTON,
    'Baseball': SPORT.BASEBALL,
    'Basketball': SPORT.BASKETBALL,
    'Beach Volley': SPORT.BEACH_VOLLEYBALL,
    'E-sport Dota': SPORT.DOTA_2,
    'ESport Counter-Strike': SPORT.COUNTER_STRIKE,
    'E-sport LoL': SPORT.LEAGUE_OF_LEGENDS,
    'Dart': SPORT.DARTS,
    'Field Hockey': SPORT.FIELD_HOCKEY,
    'Futsal': SPORT.FUTSAL,
    'Handball': SPORT.HANDBALL,
    'Icehockey': SPORT.ICE_HOCKEY,
    'Rugby': SPORT.RUGBY,
    'Snooker': SPORT.SNOOKER,
    'Soccer': SPORT.FOOTBALL,
    'Tenis stołowy': SPORT.TABLE_TENNIS,
    'Tennis': SPORT.TENNIS,
    'Volleyball': SPORT.VOLLEYBALL,
}


async def get_etoto_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get prematch events')
    resp = await c.get(CATEGORIES_URL)

    if resp.status_code != 200:
        return []

    categories = resp.json()['data']
    events = []
    categories_seen = set()
    for category in sorted(categories, key=itemgetter('level', 'categoryId')):
        category_id = category['categoryId']
        parent_category_id = category['parentCategory']
        event_count = category['eventsCount']
        seen_category = (
            category_id in categories_seen or 
            parent_category_id in categories_seen
        )
        categories_seen.add(category_id)

        if seen_category:
            continue

        if event_count > 0 and (category['level'] > 1 or event_count <= 2000):
            logger.info('TRY get %d prematch events for sport: %s and category: %s', event_count, category['sportName'], category['categoryName'])
            resp = await c.get(CATEGORY_EVENTS_URL.format(category_id=category_id))

            if resp.status_code != 200:
                continue

            category_events = resp.json()['data']

            for event_data in category_events:
                event = PrematchEvent(
                    name=event_data['eventName'],
                    date=event_data['eventStart'],
                    sport=event_data['category2Name'],
                    buk=BUK,
                    country=event_data['category1Name'],
                    competition=event_data['category3Name'],
                    open_market_count=event_data['gamesCount'],
                    markets=_get_markets(event_data['eventGames']),
                )
                events.append(event)
            
            logger.info('SUCCESS got %d prematch events for sport: %s and category: %s', event_count, category['sportName'], category['categoryName'])

            await asyncio.sleep(5) 

    logger.info('SUCCESS got %d prematch events', len(events))
    return events


async def get_etoto_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get live events')
    try:
        resp = await c.get(LIVE_URL)
    except httpx.HTTPError:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []
    
    if resp.status_code != 200:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []

    data = resp.json()['data']
    events = []

    for event_data in (d for d in data if 'games' in d):
        event_name = event_data['eventName']
        sport_name = event_data['sportName']
        sport = SPORT_MAP.get(sport_name, None)
        if sport is None:
            logger.info('skipping event: \'%s\', unknown sport: \'%s\'', event_name, sport_name)
            continue

        event_games = event_data.get('games', [])
        event = LiveEvent(
            name=event_name,
            date=event_data['eventStart'],
            sport=sport,
            score=_get_score(event_data['score']),
            buk=BUK,
            country=event_data['parentName'],
            competition=event_data['categoryName'],
            open_market_count=event_data['gamesCount'],
            markets=_get_markets(event_games),
        )
        events.append(event)

    logger.info('SUCCESS got %d live events', len(events))
    return events


########################
### HELPER FUNCTIONS ###
########################


def _get_score(score):
    return tuple(s for s in score.split(':'))


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
