import asyncio
import logging
import httpx
from pprint import pprint

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


logger = logging.getLogger(__name__)


BUK_NAME = 'ebetx'
BUK_URL = 'https://www.ebetx.pl'

PREMATCH_SPORTS_URL = 'https://sportapis.ebetx.pl/SportsOfferApi/api/sport/offer/v3/sports?OddsFilter=0'
PREMATCH_SPORT_EVENTS_URL = 'https://sportapis.ebetx.pl/SportsOfferApi/api/sport/offer/v3/sports/offer?SportIds={sport_id}&CategoryIds={category_ids}'

LIVE_EVENTS_URL = 'https://sportapis.ebetx.pl/SportsOfferApi/api/sport/offer/v3/matches/live'
# LIVE_SPORT_EVENTS_URL = 'https://sportapis.ebetx.pl/SportsOfferApi/api/sport/offer/v3/sportsmenu/live'

BUK = Buk(BUK_NAME, BUK_URL)


@timer
async def get_ebetx_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get ebetx prematch events')
    resp = await c.get(PREMATCH_SPORTS_URL)

    if resp.status_code != 200:
        logger.info('skipping ebetx prematch events, got response status code: %d', resp.status_code)
        return []
    
    sports_data = resp.json()
    events = []
    no_basic_offer_count = 0
    for sport_data in sports_data:
        logger.debug('TRY get ebetx live events for sport: %s', sport_data['Name'])
        await asyncio.sleep(5)

        sport_categories = sport_data['Categories']
        sport_category_ids = ','.join([str(category['Id']) for category in sport_categories])
        sport_id = sport_data['Id']

        resp = await c.get(PREMATCH_SPORT_EVENTS_URL.format(
            sport_id=sport_id,
            category_ids=sport_category_ids,
        ))

        if resp.status_code != 200:
            logger.info('skipping ebetx prematch sport: %s, got response status code: %d', sport_data['Name'], resp.status_code)
            continue

        events_data = resp.json()['Response'][0]
        categories = events_data['Categories']
        for category in categories:
            logger.debug('TRY get ebetx prematch events for category: %s', category['Name'])
            for league in category['Leagues']:
                logger.debug('TRY get ebetx prematch events for league: %s with %d matches', category['Name'], league['MatchesCount'])
                for match_data in league['Matches']:
                    if 'BasicOffer' not in match_data:
                        no_basic_offer_count += 1
                    event = PrematchEvent(
                        name=match_data['Description'],
                        buk=BUK,
                        date=match_data['MatchStartTime'],
                        sport=match_data['SportName'],
                        country=match_data['CategoryName'],
                        competition=match_data['LeagueName'],
                        markets=_get_markets(match_data),
                    )
                    events.append(event)

    logger.debug('ebetx prematch events with no basic offer', no_basic_offer_count)
    logger.info('SUCCESS got %d ebetx prematch events', len(events))
    return events
    

@timer
async def get_ebetx_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get ebetx live events')
    resp = await c.get(LIVE_EVENTS_URL)

    if resp.status_code != 200:
        logger.info('skipping ebetx live events, got response status code: %d', resp.status_code)
        return []
    
    sports_data = resp.json()
    events = []
    no_basic_offer_count = 0
    for sport_data in sports_data:
        logger.debug('TRY get ebetx live events for sport: %s', sport_data['Name'])
        categories = sport_data['Categories']
        for category in categories:
            logger.debug('TRY get ebetx live events for category: %s', category['Name'])
            for league in category['Leagues']:
                logger.debug('TRY get ebetx live events for league: %s with %d matches', category['Name'], league['MatchesCount'])
                for match_data in league['Matches']:
                    if 'BasicOffer' not in match_data:
                        no_basic_offer_count += 1
                    event = LiveEvent(
                        name=match_data['Description'],
                        date=match_data['MatchStartTime'],
                        buk=BUK,
                        score=_get_score(match_data['LiveMatchScore']),
                        sport=match_data['SportName'],
                        country=match_data['CategoryName'],
                        competition=match_data['LeagueName'],
                        open_market_count=match_data['OffersCount'],
                        markets=_get_markets(match_data),
                    )
                    # pprint(event)
                    events.append(event)

    logger.debug('ebetx live events with no basic offer', no_basic_offer_count)
    logger.info('SUCCESS got %d ebetx live events', len(events))
    return events
    

def _get_score(score: str) -> tuple[str, str]:
    return tuple(score.split(' : '))


def _get_markets(market_data: dict[str, any]) -> list[Market]:
    if 'BasicOffer' not in market_data:
        return []
    
    basic_offer = market_data['BasicOffer']
    return [
        Market(
            name=basic_offer['Description'],
            odds=[
                Odd(name=odd['Name'], price=odd['Odd'])
                for odd in basic_offer['Odds']
            ]
        )
    ]
