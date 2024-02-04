import asyncio
import logging
import json
from pprint import pprint
import websockets

from models import Event, PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


logger = logging.getLogger(__name__)


BETCRIS_BUK_NAME = 'betcris'
BETCRIS_BUK_URL = 'https://www.betcris.pl'
BETCRIS_WS_URL = 'wss://eu-swarm-springre.betconstruct.com/'
BETCRIS_BUK = Buk(BETCRIS_BUK_NAME, BETCRIS_BUK_URL)

GOPLUSBET_BUK_NAME = 'goplusbet'
GOPLUSBET_BUK_URL = 'https://www.goplusbet.pl'
GOPLUSBET_WS_URL = 'wss://eu-swarm-springre.trexname.com/'
GOPLUSBET_BUK = Buk(GOPLUSBET_BUK_NAME, GOPLUSBET_BUK_URL)

BETTERS_BUK_NAME = 'betters'
BETTERS_BUK_URL = 'https://www.betters.pl'
BETTERS_WS_URL = 'wss://eu-swarm-springre.betconstruct.com/'
BETTERS_BUK = Buk(BETTERS_BUK_NAME, BETTERS_BUK_URL)

MAX_MESSAGE_SIZE = 3_000_000

REQUEST_SESSION_MESSAGE = {
    'command': 'request_session',
    'params': {
        'language': 'pol',
        'site_id': '1874631',
        'source': 42,
        'is_wrap_app': False,
        'afec': 'sH5q4MZEPEG7uNja1QT1lEjqGT--6Avq9-iG',
    },
    'rid': 'request_session318101963254529'
}

SPORTS_SUBSCRIBE_MESSAGE = {
    'command': 'get',
    'params': {
        'source': 'betting',
        'what': {
            'sport': [
                'name',
                'alias',
                'id',
                'type',
                'order',
            ],
            'game': '@count',
        },
        'where': {
            'game': {
                'type': {
                    '@in':[0,2],
                },
            },
            'sport': {
                'type': {
                    '@in':[0,2,5],
                },
            },
        },
        'subscribe': False,
    },
    'rid':'SportsbookSportsMenuprematchSubscribeCmd982222402027775',
}

LIVE_EVENTS_SUBSCRIBE_MESSAGE = {
    'command': 'get',
    'params': {
        'source': 'betting',
        'what': {
            'sport': [
                'name',
                # 'alias',
                'id',
                'type',
                # 'order',
            ],
            'competition': [
                'name',
                # 'order',
                'id',
            ],
            'region': [
                'name',
                'alias',
                'order',
                'id',
            ],
            'game': [
                [
                    'id',
                    'start_ts',
                    'team1_name',
                    'team2_name',
                    # 'team1_id',
                    # 'team2_id',
                    # 'type',
                    'info',
                    'events_count',
                    'events',
                    'markets_count',
                    # 'is_started',
                    # 'is_blocked',
                    'stats',
                    # 'tv_type',
                    # 'video_id',
                    # 'video_id2',
                    # 'video_id3',
                    # 'partner_video_id',
                    # 'is_stat_available',
                    # 'game_number',
                    # 'game_info',
                    # 'last_event',
                    # 'text_info',
                ],
            ],
            'market': [
                'id',
                'name',
                'type',
                # 'order',
                'main_order',
                # 'cashout',
                # 'col_count',
                # 'display_key',
                # 'display_sub_key',
                'market_type',
                # 'name_template',
                # 'point_sequence',
                # 'sequence',
                'extra_info',
                # 'express_id',
            ],
            'event': [
                'name',
                'id',
                'price',
                'type',
                'order',
                'base',
            ],
        },
        'where': {
            'game': {
                'type': 1,
            },
            'market': {
                'display_key': {
                    '@in': [
                        'WINNER',
                        'HANDICAP',
                        'TOTALS',
                    ],
                },
                'display_sub_key': {
                    '@in': [
                        'MATCH',
                        'PERIOD',
                    ],
                },
            },
        },
        'subscribe': False,
    },
    'rid':'EULiveSportsbookSportDataSubscribeCmd72366520297999',
}


@timer
async def get_betcris_prematch_ws() -> list[PrematchEvent]:
    async with websockets.connect(BETCRIS_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(SPORTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = await _get_prematch_sports_events(websocket, sports_data, BETCRIS_BUK)
        return events


@timer
async def get_betcris_live_ws() -> list[LiveEvent]:
    async with websockets.connect(BETCRIS_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(LIVE_EVENTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = _get_live_sports_events(sports_data, BETCRIS_BUK)
        # pprint(events[0])
        return events


@timer
async def get_goplusbet_prematch_ws() -> list[PrematchEvent]:
    async with websockets.connect(GOPLUSBET_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(SPORTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = await _get_prematch_sports_events(websocket, sports_data, GOPLUSBET_BUK)
        return events


@timer
async def get_goplusbet_live_ws() -> list[LiveEvent]:
    async with websockets.connect(GOPLUSBET_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(LIVE_EVENTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = _get_live_sports_events(sports_data, GOPLUSBET_BUK)
        return events


@timer
async def get_betters_prematch_ws() -> list[PrematchEvent]:
    async with websockets.connect(BETTERS_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(SPORTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = await _get_prematch_sports_events(websocket, sports_data, BETTERS_BUK)
        return events


@timer
async def get_betters_live_ws() -> list[LiveEvent]:
    async with websockets.connect(BETTERS_WS_URL, max_size=MAX_MESSAGE_SIZE) as websocket:
        await websocket.send(json.dumps(REQUEST_SESSION_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        await websocket.send(json.dumps(LIVE_EVENTS_SUBSCRIBE_MESSAGE))
        answer = await websocket.recv()
        answer = json.loads(answer)

        sports_data = answer['data']['data']['sport']
        # pprint([sport['name'] for sport in sports_data.values()])
        events = _get_live_sports_events(sports_data, BETTERS_BUK)
        return events


async def _get_prematch_sports_events(websocket, sports_data: dict[str, any], buk: Buk) -> list[PrematchEvent]:
    sports_len = len(sports_data)
    events = []
    for i, sport_data in enumerate(sports_data.values()):
        sport_id = str(sport_data['id'])
        sport_name = sport_data['name'].strip()
        sport_alias = sport_data['alias'].strip()

        # print(f'[{i+1}/{sports_len}] {sport_name}: ', end='')
        sport_events = await _get_prematch_sport_events(websocket, sport_id, sport_name, sport_alias, buk)
        # print(len(sport_events))

        events += sport_events

        await asyncio.sleep(1)
    return events


def _get_live_sports_events(sports_data: dict[str, any], buk: Buk) -> list[LiveEvent]:
    sports_len = len(sports_data)
    events = []
    for i, sport_data in enumerate(sports_data.values()):
        sport_name = sport_data['name'].strip()

        # print(f'[{i+1}/{sports_len}] {sport_name}: ', end='')
        sport_events =  _get_live_sport_events(sport_data, sport_name, buk)
        # print(len(sport_events))

        events += sport_events
    return events
    

async def _get_prematch_sport_events(websocket, sport_id: str, sport_name: str, sport_alias: str, buk: Buk) -> list[PrematchEvent]:
    message = _get_sport_game_list_subscribe_message(sport_alias) 
    await websocket.send(json.dumps(message))

    answer = await websocket.recv()
    answer  = json.loads(answer)

    sport_data = answer['data']['data']['sport'][sport_id]
    sport_events = []
    for region_data in sport_data['region'].values():
        region = region_data['name']
        for competition_data in region_data['competition'].values():
            competition = competition_data['name']
            for event_data in competition_data['game'].values():
                event = _get_event(event_data, sport_name, region, competition, buk)
                if event is None:
                    continue
                sport_events.append(event)
    return sport_events 


def _get_live_sport_events(sport_data: dict, sport_name: str, buk: Buk) -> list[LiveEvent]:
    sport_events = []
    for region_data in sport_data['region'].values():
        region = region_data['name']
        for competition_data in region_data['competition'].values():
            competition = competition_data['name']
            for event_data in competition_data['game'].values():
                event = _get_event(event_data, sport_name, region, competition, buk)
                if event is None:
                    continue
                sport_events.append(event)
    return sport_events 


def _get_event(event_data: dict[str, any], sport: str, region: str, competition: str, buk: Buk) -> Event:
    is_live = False
    if 'info' in event_data:
        is_live = True

    if 'team1_name' not in event_data:
        return None
    team_1 = event_data['team1_name']

    name = None
    if 'team2_name' not in event_data:
        name = team_1
    else:
        team_2 = event_data['team2_name']
        name = f'{team_1} - {team_2}'
        
    if is_live:
        info = event_data['info']
        # is_game_state = 'current_game_state' in info
        # is_game_time = 'current_game_time' in info

        # current_game_state = None
        # match (is_game_state, is_game_time):
        #     case (True, _):
        #         current_game_state = info['current_game_state']
        #     case (False, True):
        #         current_game_state = info['current_game_time']
        #     case (False, False):
        #         current_game_state = 'x' 
        score = None
        if 'score1' in info:
            score = (info['score1'], info['score2'])
        # event['event_time_state'] = current_game_state

        event = LiveEvent(
            name=name,
            buk=buk,
            sport=sport,
            country=region,
            competition=competition,
            date=event_data['start_ts'] ,
            score=score,
            open_market_count=event_data['markets_count'],
            markets=_get_markets(event_data['market'].values()),
        )
        return event
    
    event = PrematchEvent(
        name=name,
        buk=buk,
        sport=sport,
        country=region,
        competition=competition,
        date=event_data['start_ts'] ,
        open_market_count=event_data['markets_count'],
        markets=_get_markets(event_data['market'].values()),
    )
    
    return event


def _get_markets(markets_data: dict[str, any]) -> list[Market]:
    markets = []
    for market_data in markets_data:
        market = Market(
            name=market_data['name'],
            odds=[
                Odd(name=odd['name'], price=odd['price'])
                for odd in market_data['event'].values()
            ],
        )
        markets.append(market)
    return markets


def _get_sport_game_list_subscribe_message(sport_alias: str) -> dict[str, any]:
    return {
        'command': 'get',
        'params': {
            'source': 'betting',
            'what': {
                'sport': [
                    'id',
                    'name',
                    'alias',
                ],
                'region': [
                    'id',
                    'name',
                    'alias',
                    # 'order',
                ],
                'competition': [
                    'id',
                    'name',
                    # 'order',
                ],
                'game':[
                    [
                        'id',
                        'team1_name',
                        'team2_name',
                        # 'team1_id',
                        # 'team2_id',
                        # 'order',
                        'start_ts',
                        'markets_count',
                        # 'is_blocked',
                        # 'show_type',
                        # 'sportcast_id',
                        # 'is_stat_available',
                        # 'game_number',
                    ],
                ],
                'market': [
                    'name',
                    # 'order',
                    'type',
                    'id',
                    # 'base',
                    # 'col_count',
                    # 'main_order',
                    # 'express_id',
                    # 'prematch_express_id',
                ],
                'event': [
                    'id',
                    'name'
                    ,'price',
                    # 'base',
                    # 'order',
                    # 'type_1',
                ],
            },
            'where': { 
                'game': {
                    '@or': [
                        {
                            'type': {
                                '@in': [0,2],
                            },
                        },
                        {
                            'visible_in_prematch': 1,
                        },
                    ],
                },
                'market': {
                    'type': 'P1XP2',
                },
                'sport': {
                    'alias': sport_alias,
                    'type': {
                        '@in': [0,2,5],
                    },
                },
            },
            'subscribe': False,
        },
        'rid': 'GameListSubscribeCmd642595226244015',
    }
