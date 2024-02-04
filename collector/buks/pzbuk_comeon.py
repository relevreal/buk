import asyncio
import logging
import httpx
from pprint import pprint
import websockets
import json

from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


logger = logging.getLogger(__name__)


PZBUK_BUK_NAME = 'pzbuk'
PZBUK_BUK_URL = 'https://www.pzbuk.pl'
PZBUK_BUK = Buk(PZBUK_BUK_NAME, PZBUK_BUK_URL)

PZBUK_SPORTS_URL = 'https://www.pzbuk.pl/sportsbook-api/api/sports?franchiseCode=POLAND_PZBUK&locale=pl'
PZBUK_SPORT_LEAGUES_URL = 'https://www.pzbuk.pl/sportsbook-api/api/leaguesByEvents?eventTypes=Fixture&eventTypes=AggregateFixture&eventTypes=AntePostRace&eventTypes=DayOfEventRace&franchiseCode=POLAND_PZBUK&isLive=true&locale=pl&sportId={sport_id}'
PZBUK_MAIN_SPORT_MARKETS_URL = 'https://www.pzbuk.pl/sportsbook-api/api/markets/main-market-types?franchiseCode=POLAND_PZBUK&locale=pl&sportId={sport_id}'
PBZUK_WS_URL = 'wss://www.pzbuk.pl/sportsbook-api/websocket?franchiseCode=POLAND_PZBUK&locale=pl'

COMEON_BUK_NAME = 'comeon'
COMEON_BUK_URL = 'https://www.comeon.pl'
COMEON_BUK = Buk(COMEON_BUK_NAME, COMEON_BUK_URL)

COMEON_SPORTS_URL = 'https://www.comeon.pl/sportsbook-api/api/sports?franchiseCode=POLAND_COMEON&locale=pl'
COMEON_SPORT_LEAGUES_URL = 'https://www.comeon.pl/sportsbook-api/api/leaguesByEvents?eventTypes=Fixture&eventTypes=AggregateFixture&eventTypes=AntePostRace&eventTypes=DayOfEventRace&franchiseCode=POLAND_COMEON&isLive=true&locale=pl&sportId=1'
COMEON_MAIN_SPORT_MARKETS_URL = 'https://www.comeon.pl/sportsbook-api/api/markets/main-market-types?franchiseCode=POLAND_COMEON&locale=pl&sportId={sport_id}'
COMEONE_WS_URL = 'wss://www.comeon.pl/sportsbook-api/websocket?franchiseCode=POLAND_COMEON&locale=pl'

FIRST_MESSAGE_HEX = '000000000400000100000000ea600001d4c01c6d6573736167652f782e72736f636b65742e726f7574696e672e7630106170706c69636174696f6e2f6a736f6e'

GET_EVENTS_MESSAGE = b'\x00\x00\x00\x05\x19\x00\x00\x00\x002\x00\x00\x08\x07/events'
ANSWER_PREFIX = b'\x00\x00\x00\x05( '
ANSWER_PREFIX_LEN = len(ANSWER_PREFIX)


def _get_message(sport_ids: list[str], league_ids: list[str]) -> dict[str, any]:
    message = {
        'filters': {
            # 'eventIds': None,
            # 'eventStartDateFrom': None,
            # 'eventStartDateTo': None,
            'eventTypes': [
                'Fixture',
                'AggregateFixture',
                'AntePostRace',
                'DayOfEventRace',
            ],
            'isLive': True,
            'leagueIds': league_ids,
            # 'marketIds': None,
            # 'marketNames': None,
            # 'marketTypeIds': market_type_ids,
            # 'marketTypeIds': [
            #     "1_0","1_39","1_0","1_39","a_232","a_314","2_0","2_39","a_1038",
            # ],
            # 'selectionIds': None,
            # 'sportIds': None,
            # 'sportIds': sport_ids[3:4],
            # 'type': 'UPCOMING',
            'type': 'LIVE',
        },
    }
    return message


@timer
async def get_pzbuk_prematch_ws(c: httpx.AsyncClient):
    pass


@timer
async def get_pzbuk_live_ws(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get pzbuk live events')
    resp = await c.get(PZBUK_SPORTS_URL)
    
    if resp.status_code != 200:
        logger.info('skipping pzbuk live events, got response status code: %d', resp.status_code)
        return []

    sports_data = resp.json()
    live_sport_ids = [
        sport_data['id']
        for sport_data in sports_data
        if sport_data['liveEventCount']
    ]
    # pprint(sports_data)
    # print(live_sport_ids)
    # exit(1)

    # market_tasks = [
    #     c.get(PZBUK_MAIN_SPORT_MARKETS_URL.format(sport_id=sport_id))
    #     for sport_id in live_sport_ids[:1]
    # ]
    league_tasks = [
        c.get(PZBUK_SPORT_LEAGUES_URL.format(sport_id=sport_id))
        for sport_id in live_sport_ids
    ] 
    # n_markets = len(market_tasks)
    # results = await asyncio.gather(*market_tasks, *league_tasks)
    results = await asyncio.gather(*league_tasks)
    # market_type_ids = set()
    # for result in results[:n_markets]:
    #     if result.status_code != 200:
    #         logger.info('skipping pzbuk live events, got response status code: %d, when getting sport markets', resp.status_code)
    #         continue
    #     markets_data = result.json()
    #     for market_data in markets_data:
    #         market_type_ids.update(market_data['marketTypeIds'])

    sport_league_ids = []
    next_league_ids = []
    curr_leagues_events_num = 0
    for result in results:
        if result.status_code != 200:
            logger.info('skipping pzbuk live events, got response status code: %d, when getting sport leagues', resp.status_code)
            continue
        leagues_data = result.json()
        for league_data in leagues_data:
            event_count = league_data['eventCount']
            league_id = league_data['id']
            print(league_id, event_count)
            if (curr_leagues_events_num + event_count) > 10:
                sport_league_ids.append(next_league_ids)
                next_league_ids = [league_id]
                curr_leagues_events_num = 0
            else:
                next_league_ids.append(league_id)
                curr_leagues_events_num += event_count
    if next_league_ids:
        sport_league_ids.append(next_league_ids)

    event_tasks_n = len(sport_league_ids)
    
    if not event_tasks_n:
        return []
    
    event_tasks_done = 0
    curr_league_ids = sport_league_ids[event_tasks_done]
    events = []
    markets_data = []
    odds_data = []
    events_data = []
    print(sport_league_ids)
    async with websockets.connect(PBZUK_WS_URL) as ws:
        logger.debug('TRY get pzbuzk websocket events')
        # message = _get_message(live_sport_ids, None, list(market_type_ids))
        await ws.send(bytearray.fromhex(FIRST_MESSAGE_HEX))
        get_events_tasks = []
        for league_ids in sport_league_ids:
            message = _get_message(None, league_ids)
            byte_message = bytes(json.dumps(message), encoding='utf-8')
            get_events_message = GET_EVENTS_MESSAGE + byte_message
            await ws.send(get_events_message)
            answer = await ws.recv()
            decoded = json.loads(answer[ANSWER_PREFIX_LEN:].decode('utf-8'))
            # pprint(decoded)
        exit(1)
        # message = _get_message(live_sport_ids, curr_league_ids)
        # pprint(message)
        result = await asyncio.gather(*get_events_tasks)
        print('result:', result)
        while event_tasks_done < event_tasks_n:
            print('event tasks done:', event_tasks_done)
            answer = await ws.recv()
            decoded = json.loads(answer[ANSWER_PREFIX_LEN:].decode('utf-8'))

            print('got answer')

            # if not answer.startswith(ANSWER_PREFIX):
            #     continue

            if decoded[0]['type'] != 'INITIAL_STATE':
                print('got not initial state')
                pprint(decoded)
                # exit(1)
                continue

            data = decoded[0]['payload']
            print('got answer jej')
            if 'markets' not in data:
                pprint(decoded)
                print('no markets')
                exit(1)
            # pprint(data)
            markets_data += data['markets']
            odds_data += data['selections']
            events_data += data['events']

            event_tasks_done += 1
            curr_league_ids = sport_league_ids[event_tasks_done]
            # message = _get_message(live_sport_ids, curr_league_ids)
        
        markets_dict = {}
        for market_data in markets_data:
            market_type = market_data['marketType']
            event_id = market_data['eventId']
            market_dict = {
                'name': market_type['name'],
                'odd_ids': [(market_data['id'], int(odd['id'])) for odd in market_type['selectionsTemplate']],
            }

            if event_id in markets_dict:
                markets_dict[event_id].append(market_dict)
            else:
                markets_dict[event_id] = [market_dict]

        odds_data = data['selections']
        odds_dict = {}
        for odd_data in odds_data:
            odds_dict[(odd_data['marketId'], odd_data['templateId'])] = Odd(name=odd_data['name'], price=odd_data['trueOdds'])
        
        # events_data = data['events']
        print('events data len:', len(events_data))
        exit(1)
        
        for event_data in events_data:
            if not event_data['isLive']:
                continue
            event_id = event_data['id']
            open_market_count = sum(mg['marketsCount'] for mg in event_data['marketGroups'])
            markets = _get_markets(markets_dict, odds_dict, event_id)
            event = LiveEvent(
                name=event_data['eventName'],
                buk=PZBUK_BUK,
                sport=event_data['sportName'],
                competition=event_data['leagueName'],
                date=event_data['startingOn'],
                score=(event_data['gameScore']['homeScore'], event_data['gameScore']['awayScore']),
                # should change to region probably
                country=event_data['regionName'],
                open_market_count=open_market_count,
                markets=markets,
            )
            events.append(event)

        logger.debug('SUCCESS get pzbuk websocket %d events', len(events))

    pprint(events[-1])
    print(len(events))
    logger.info('SUCCESS got %d pzbuk live events', len(events))
    return events


@timer
async def get_comeon_prematch_ws():
    pass


@timer
async def get_comeon_live_ws(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get comeon live events')
    resp = await c.get(COMEON_SPORTS_URL)
    
    if resp.status_code != 200:
        logger.info('skipping pzbuk live events, got response status code: %d', resp.status_code)
        return []

    sports_data = resp.json()
    live_sport_ids = [
        sport_data['id']
        for sport_data in sports_data
        if sport_data['liveEventCount']
    ]

    market_tasks = [
        c.get(COMEON_MAIN_SPORT_MARKETS_URL.format(sport_id=sport_id))
        for sport_id in live_sport_ids
    ] 
    results = await asyncio.gather(*market_tasks)
    market_type_ids = set()
    for result in results:
        if result.status_code != 200:
            logger.info('skipping pzbuk live events, got response status code: %d, when getting sport markets', resp.status_code)
            continue
        markets_data = result.json()
        for market_data in markets_data:
            market_type_ids.update(market_data['marketTypeIds'])
    
    events = []
    async with websockets.connect(PBZUK_WS_URL) as ws:
        logger.debug('TRY get pzbuzk websocket events')
        message = _get_message(live_sport_ids, list(market_type_ids))
        await ws.send(bytearray.fromhex(FIRST_MESSAGE_HEX))
        await ws.send(GET_EVENTS_MESSAGE + bytes(json.dumps(message), encoding='utf-8'))
        answer = await ws.recv()

        decoded = json.loads(answer[ANSWER_PREFIX_LEN:].decode('utf-8'))
        data = decoded[0]['payload']
        markets_data = data['markets']
        odds_data = data['selections']
        
        markets_dict = {}
        for market_data in markets_data:
            market_type = market_data['marketType']
            event_id = market_data['eventId']
            market_dict = {
                'name': market_type['name'],
                'odd_ids': [(market_data['id'], int(odd['id'])) for odd in market_type['selectionsTemplate']],
            }

            if event_id in markets_dict:
                markets_dict[event_id].append(market_dict)
            else:
                markets_dict[event_id] = [market_dict]

        odds_data = data['selections']
        odds_dict = {}
        for odd_data in odds_data:
            odds_dict[(odd_data['marketId'], odd_data['templateId'])] = Odd(name=odd_data['name'], price=odd_data['trueOdds'])
        
        events_data = data['events']
        for event_data in events_data:
            if not event_data['isLive']:
                continue
            event_id = event_data['id']
            open_market_count = sum(mg['marketsCount'] for mg in event_data['marketGroups'])
            markets = _get_markets(markets_dict, odds_dict, event_id)
            event = LiveEvent(
                name=event_data['eventName'],
                buk=PZBUK_BUK,
                sport=event_data['sportName'],
                competition=event_data['leagueName'],
                date=event_data['startingOn'],
                score=(event_data['gameScore']['homeScore'], event_data['gameScore']['awayScore']),
                # should change to region probably
                country=event_data['regionName'],
                open_market_count=open_market_count,
                markets=markets,
            )
            events.append(event)

        logger.debug('SUCCESS get comeon websocket %d events', len(events))

    pprint(events[-1])
    print(len(events))
    logger.info('SUCCESS got %d comeon live events', len(events))
    return events


def _get_markets(markets_dict: dict[str, any], odds_dict: dict[str, any], event_id: int) -> list[Market]:
    markets = []
    for market_dict in markets_dict.get(event_id, []):
        odds = []
        for odd_id in market_dict['odd_ids']:
            odd = odds_dict.get(odd_id, None)
            if odd is None:
                continue
            odds.append(odd)

        market = Market(
            name=market_dict['name'],
            odds=odds,
        )
        markets.append(market)

    return markets
