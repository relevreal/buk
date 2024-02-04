import asyncio
import logging
import datetime as dt
import httpx
from pprint import pprint

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


logger = logging.getLogger(__name__)


BUK_NAME = 'superbet'
BUK_URL = 'https://www.superbet.pl'
BUK = Buk(BUK_NAME, BUK_URL)

SPORTS_URL = 'https://superbet-content.freetls.fastly.net/cached-superbet/sports-offer/sports/pl-PL'
STRUCT_URL = 'https://production-superbet-offer-pl.freetls.fastly.net/v2/pl-PL/struct'

PREMATCH_URL = 'https://production-superbet-offer-pl.freetls.fastly.net/v2/pl-PL/events/by-date?offerState=prematch&startDate={start_date}&endDate={end_date}'
# PREMATCH_URL = 'https://production-superbet-offer-pl.freetls.fastly.net/v2/pl-PL/events/by-date?offerState=prematch&startDate=2024-01-14+12:44:00&endDate=2025-01-15+08:00:00'

# LIVE_URL = 'https://production-superbet-offer-pl.freetls.fastly.net/v2/pl-PL/events/by-date?currentStatus=active&offerState=live&startDate=2024-01-08+08:45:00'
LIVE_URL = 'https://production-superbet-offer-pl.freetls.fastly.net/v2/pl-PL/events/by-date?currentStatus=active&offerState=live&startDate={start_date}'

QUERY_DATE_FORMAT = '%Y-%m-%d+%H:%M:%S'
EVENT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


@timer
async def get_superbet_prematch(c: httpx.AsyncClient) -> list[PREMATCH_URL]:
    logger.info('TRY get superbet prematch events')
    start_date = dt.datetime.now()
    end_date = start_date + dt.timedelta(days=365)
    start_date_str = start_date.strftime(QUERY_DATE_FORMAT)
    end_date_str = end_date.strftime(QUERY_DATE_FORMAT)
    
    sports_task = c.get(STRUCT_URL)
    events_task = c.get(PREMATCH_URL.format(
        start_date=start_date_str,
        end_date=end_date_str,
    ))
    result = await asyncio.gather(sports_task, events_task)

    if result[0].status_code != 200 or result[1].status_code != 200:
        logger.info('skipping superbet prematch events, got error response status code (%d, %d) when getting struct and live events data', result[0].status_code, result[1].status_code)
        return []

    struct_data = result[0].json()['data']
    sports_data = struct_data['sports']
    categories_data = struct_data['categories']
    tournaments_data = struct_data['tournaments']
    events_data = result[1].json()['data']

    sports_dict = {
        int(sport_data['id']): sport_data['localNames']['pl-PL']
        for sport_data in sports_data
    }

    categories_dict = {
        int(category_data['id']): category_data['localNames']['pl-PL']
        for category_data in categories_data
    }

    tournaments_dict = {
        int(tournament_data['id']): tournament_data['localNames']['pl-PL']
        for tournament_data in tournaments_data
    }

    events = []
    for event_data in events_data:
        event = {
            'name': event_data['matchName'],
            'sport': sports_dict[event_data['sportId']],
            'category': categories_dict[event_data['categoryId']],
            'tournament': tournaments_dict[event_data['tournamentId']],
            'date': event_data['matchDate'],
            'open_markets_count': event_data['marketCount'],
            'markets': _get_markets(event_data['odds']),
        }
        events.append(event)

    logger.info('SUCCESS got %d superbet prematch events', len(events))
    return events


@timer
async def get_superbet_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get superbet live events')

    start_date = dt.datetime.now()
    start_date_str = start_date.strftime(QUERY_DATE_FORMAT)
    
    sports_task = c.get(STRUCT_URL)
    events_task = c.get(LIVE_URL.format(start_date=start_date_str))
    result = await asyncio.gather(sports_task, events_task)

    if result[0].status_code != 200 or result[1].status_code != 200:
        logger.info('skipping superbet live events, got error response status code (%d, %d) when getting struct and live events data', result[0].status_code, result[1].status_code)
        return []

    struct_data = result[0].json()['data']
    sports_data = struct_data['sports']
    categories_data = struct_data['categories']
    tournaments_data = struct_data['tournaments']
    events_data = result[1].json()['data']

    sports_dict = {
        int(sport_data['id']): sport_data['localNames']['pl-PL']
        for sport_data in sports_data
    }

    categories_dict = {
        int(category_data['id']): category_data['localNames']['pl-PL']
        for category_data in categories_data
    }

    tournaments_dict = {
        int(tournament_data['id']): tournament_data['localNames']['pl-PL']
        for tournament_data in tournaments_data
    }

    events = []
    for event_data in events_data:
        metadata = event_data.get('metadata', None)
        if metadata is None:
            continue
        home_score = metadata.get('homeTeamScore')
        if home_score is None:
            score = None
        else:
            away_score = metadata.get('awayTeamScore')
            if away_score is None:
                score = (home_score)
            else:
                score = (home_score, away_score)
        
        event = LiveEvent(
            name=event_data['matchName'],
            buk=BUK,
            sport=sports_dict[event_data['sportId']],
            competition=tournaments_dict[event_data['tournamentId']],
            country=categories_dict[event_data['categoryId']],
            score=score,
            date=_get_date(event_data['matchDate']),
            open_market_count=event_data['marketCount'],
            markets=_get_markets(event_data['odds']),
        )
        events.append(event)

    # pprint(events[-1])
    logger.info('SUCCESS got %d superbet live events', len(events))
    return events


def _get_markets(market_data: dict[str, any]) -> list[Market]:
    if not market_data:
        return []
    market = Market( 
        name=market_data[0]['marketName'],
        odds=[
            Odd(name=odd['name'], price=odd['price']) 
            for odd in market_data
        ]
    )
    markets = [market]
    return markets


def _get_date(date_str: str) -> str:
    return date_str.replace(' ', 'T') + 'Z'