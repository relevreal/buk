import logging
from enum import Enum
from pprint import pprint

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from db.sports import SPORT
from db.utils import to_unix_time

import httpx

from utils import timer


logger = logging.getLogger(__name__)


BUK_NAME = 'betclic'
BUK_URL = 'https://www.betclic.pl'
PREMATCH_URL = 'https://offer.cdn.begmedia.com/api/pub/v4/sports/{sport_id}?application=2048&countrycode=pl&hasSwitchMtc=true&language=pa&limit=1000&offset=0&sitecode=plpa&sortBy=ByLiveRankingPreliveDate'
LIVE_URL = 'https://offer.cdn.begmedia.com/api/pub/v1/lives?application=2048&countrycode=pl&language=pa&limit=1000&offset=0&sitecode=plpa&sortBy=ByLiveRankingPreliveDate'

BUK = Buk(BUK_NAME, BUK_URL)

class Sport(Enum):
    # FOOTBALL = 1
    # BASKETBALL = 4
    # SUPER_BETS = 99
    # BADMINTON = 27
    # BANDY = 88
    # BASEBALL = 20
    # BIATHLON = 62
    # BOX = 16
    # BOWLS = 77
    # DART = 53
    # ESPORT = 102
    # F1 = 3
    # AMERICAN_FOOTBALL = 14
    # AUSTRALIAN_FOOTBALL = 73
    GOLF = 7
    # HOCKEY = 13
    # CYCLING = 6
    # CRICKET = 11
    # NASCAR = 24
    # HANDBALL = 9
    # WATER_POLO = 33
    # RUGBY_13 = 52
    # RUGBY_15 = 5
    # VOLEYBALL = 8
    # SNOOKER = 54
    # MARTIAL_ARTS = 23
    # TABLE_TENNIS = 32
    # ROLLEY_HOCKEY = 89
    # MOTORCYCLE_RACING = 15
    # SPECIAL_BETS = 80
    # MOTORCYCLE_SPEEDWAY = 55


SPORT_MAP = {
    'Badminton': SPORT.BADMINTON,
    'Baseball': SPORT.BASEBALL,
    'Dart': SPORT.DARTS,
    'Esport': SPORT.ESPORT,
    'Futsal': SPORT.FUTSAL,
    'Hokej': SPORT.ICE_HOCKEY,
    'Koszykówka': SPORT.BASKETBALL,
    'Narciarstwo Alpejskie': SPORT.ALPINE_SKIING,
    'Piłka nożna': SPORT.FOOTBALL,
    'Piłka ręczna': SPORT.HANDBALL,
    'Piłka wodna': SPORT.WATERBALL,
    'Siatkówka': SPORT.VOLLEYBALL,
    'Siatkówka plażowa': SPORT.BEACH_VOLLEYBALL,
    'Snooker': SPORT.SNOOKER,
    'Rugby XV': SPORT.RUGBY,
    'Tenis': SPORT.TENNIS,
    'Tenis stołowy': SPORT.TABLE_TENNIS,
}


async def get_betclic_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get prematch events')
    events = []
    for sport in Sport:
        logger.debug('TRY get betclic prematch events for %s sport', sport.name)
        sport_events = await _get_sport_prematch(c, sport.value)
        logger.debug('SUCCESS got %d prematch events for %s sport', len(sport_events), sport.name)
        events += sport_events
    logger.info('SUCCESS got %d prematch events', len(events))
    return events


@timer
async def get_betclic_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get live events')
    try:
        resp = await c.get(LIVE_URL)
    except httpx.HTTPError as exc:
        logger.error('Error while getting live events', exc_info=exc)
        return []

    if resp.status_code != 200:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []    

    events_data = resp.json()
    events = []
    for event_data in events_data:
        competition_data = event_data['competition']
        country_data = competition_data.get('country', None)
        if country_data is None:
            country = None
        else:
            country = country_data.get('code', None) 

        sport_name = competition_data['sport']['name'] 
        sport = SPORT_MAP.get(sport_name, None)
        event_name = event_data['name']
        if sport is None:
            logger.info('skipping event: \'%s\', unknown sport: \'%s\'', event_name, sport_name)
            continue

        event = LiveEvent(
            name=event_name,
            # add 1 hour
            date= to_unix_time(event_data['date']) + 3600,
            score= _get_score(event_data),
            buk=BUK,
            sport=sport,
            country=country,
            competition=competition_data['name'],
            open_market_count=event_data['open_market_count'],
            markets=_get_markets(event_data['grouped_markets']),
        )
        events.append(event)
    logger.info('SUCCESS got %d live events', len(events))
    return events


########################
### HELPER FUNCTIONS ###
########################


def _get_score(event_data):
    if 'live_data' not in event_data:
        return None
    scoreboard = event_data['live_data']['scoreboard']
    score_data = scoreboard.get('current_score', None)
    if score_data is None:
        return None
    return tuple(score for score in score_data.values())


@timer
async def _get_sport_prematch(c: httpx.AsyncClient, sport_id: int) -> list[PrematchEvent]:
    response = await c.get(PREMATCH_URL.format(sport_id=sport_id))
    events_data = response.json()
    events = []
    for event_data in events_data['matches']:
        if event_data['is_live']:
            continue
        competition_data = event_data['competition']
        event = PrematchEvent(
            name=event_data['name'],
            date= event_data['date'],
            sport=competition_data['sport']['name'],
            buk=BUK,
            country=competition_data['country']['code'],
            competition=competition_data['name'],
            open_market_count=event_data['open_market_count'],
            markets=_get_markets(event_data['grouped_markets']),
        )
        events.append(event)
    return events


def _get_markets(grouped_markets: dict[str, any]) -> list[Market]:
    markets = []
    for group_market in grouped_markets:
        for market_data in group_market['markets']:
            market = Market(
                name=market_data['name'],
                odds=[Odd(name=odd[0]['name'], price=odd[0]['odds'])
                    for odd in market_data['selections']  
                ]
            )
            markets.append(market)
    return markets
