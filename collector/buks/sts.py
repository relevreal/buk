import logging
import datetime as dt
import httpx
from pprint import pprint

from db.sports import SPORT
from models import PrematchEvent, LiveEvent, Buk, Market, Odd
from utils import timer


BUK_NAME = 'sts'
BUK_URL = 'https://www.sts.pl'
PREMATCH_URL = 'https://api.sts.pl/web/v1/offer/prematch?to={to}&lang=pl'
OFFER_URL = "https://spoon.sts.pl/offer/?lang=pl"
MAIN_OPPORTUNITIES_URL = "https://spoon.sts.pl/main_opportunities/?lang=pl"

BUK = Buk(name=BUK_NAME, url=BUK_URL)


logger = logging.getLogger(__name__)


PREMATCH_HEADERS = {
    'authority': 'api.sts.pl',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en;q=0.9,pl-PL;q=0.8,pl;q=0.7,en-US;q=0.6',
    'content-type': 'application/json',
    # 'if-modified-since': 'Sat, 13 Jan 2024 12:48:58 GMT',
    'origin': 'https://www.sts.pl',
    'referer': 'https://www.sts.pl/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-api-key': '5ZU3zqUqo8WjprFgAM',
    'x-platform': 'desktop-rwd',
    'x-request-uuid': '9afcf45a-c97f-441b-b668-52fd7d036872',
}


OFFER_HEADERS = {
    'authority': 'spoon.sts.pl',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en;q=0.9,pl-PL;q=0.8,pl;q=0.7,en-US;q=0.6',
    'if-modified-since': 'Sat, 13 Jan 2024 13:55:21 GMT',
    'origin': 'https://www.sts.pl',
    'referer': 'https://www.sts.pl/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


OFFER_PARAMS = {
    'lang': 'pl',
}


SPORT_MAP = {
    'Badminton': SPORT.BADMINTON,
    'Baseball': SPORT.BASEBALL,
    'Biathlon': SPORT.BIATHLON,
    'Biegi Narciarskie': SPORT.CROSS_COUNTRY_SKIING,
    'Counter Strike': SPORT.COUNTER_STRIKE,
    'Darts': SPORT.DARTS,
    'Dota 2': SPORT.DOTA_2,
    'ePiłka nożna': SPORT.FIFA,
    'Formuła 1': SPORT.FORMULA_1,
    'Futsal': SPORT.FUTSAL,
    'Golf': SPORT.GOLF,
    'Hokej na Lodzie': SPORT.ICE_HOCKEY,
    'Koszykówka': SPORT.BASKETBALL,
    'League of Legends': SPORT.LEAGUE_OF_LEGENDS,
    'Narciarstwo alpejskie': SPORT.ALPINE_SKIING,
    'Piłka nożna': SPORT.FOOTBALL,
    'Piłka Nożna': SPORT.FOOTBALL,
    'Piłka ręczna': SPORT.HANDBALL,
    'Piłka Ręczna': SPORT.HANDBALL,
    'Rugby': SPORT.RUGBY,
    'Saneczkarstwo': SPORT.LUGE,
    'Siatkówka': SPORT.VOLLEYBALL,
    'Siatkówka Plażowa': SPORT.BEACH_VOLLEYBALL,
    'Skoki Narciarskie': SPORT.SKI_JUMPING,
    'Snooker': SPORT.SNOOKER,
    'Tenis': SPORT.TENNIS,
    'Tenis Stołowy': SPORT.TABLE_TENNIS,
    'Żużel': SPORT.SLAG,
}


@timer
async def get_sts_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get prematch events')
    to = dt.datetime.now() + dt.timedelta(days=180)
    to_str = to.strftime('%Y-%m-%dT%H:%M')
    resp = await c.get(PREMATCH_URL.format(to=to_str), headers=PREMATCH_HEADERS)

    if resp.status_code != 200:
        return []

    events_data = resp.json()
    events = []
    for event_data in events_data:
        event = PrematchEvent(
            name=event_data['markets'][0]['name'],
            sport=event_data['sport']['name'],
            buk=BUK,
            competition=event_data['league']['name'],
            date=event_data['start_at'],
            country=event_data['region']['name'],
            open_market_count=event_data['markets_count'],
            markets=[
                Market(
                    name=market_data['type_name'],
                    odds=[
                        Odd(
                            name=odd['selection']['long_name'],
                            price=odd['value'],
                        )
                        for odd in market_data['odds']
                    ],
                )
                for market_data in event_data['markets']
            ]
        )
        events.append(event)
    
    logger.info('SUCCESS got %d prematch events', len(events))
    return events


@timer
async def get_sts_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get live events')
    try:
        resp = await c.get(MAIN_OPPORTUNITIES_URL)
    except httpx.HTTPError:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []
    
    if resp.status_code != 200:
        logger.error('skipping live events, got response status code: %d', resp.status_code)
        return []

    main_data = resp.json()
    oppties_data = main_data['oppties']
    odds_data = main_data['odds']

    odds_dict = {}
    for odd_data in odds_data:
        iop = odd_data['iop']
        odd = Odd(name=odd_data.get('otl', 'name'), price=odd_data.get('ov', -1.0))
        if iop in odds_dict:
            odds_dict[iop].append(odd)
        else:
            odds_dict[iop] = [odd]


    event_markets = {} 
    for oppt_data in oppties_data:
        iop = oppt_data.get('iop', None)
        ig = oppt_data.get('ig', None)
        otn =  oppt_data.get('otn', None)
        if any(x is None for x in (iop, ig, otn)):
            continue
        market = Market(
            name=otn,
            odds=odds_dict.get(iop, []),
        )
        if ig in event_markets:
            event_markets[ig].append(market)
        else:
            event_markets[ig] = [market]

    resp = await c.get(OFFER_URL, params=OFFER_PARAMS, headers=OFFER_HEADERS)

    if resp.status_code != 200:
        return []

    events_data = resp.json()
    events = []
    for event_data in events_data:
        event_state = event_data['gpn']
        if event_state == 'Nierozpoczęty' or event_state == 'Mecz zakończony':
            continue

        event_name = event_data['mn']
        sport_name = event_data['sn']
        sport = SPORT_MAP.get(sport_name, None)
        if sport is None:
            logger.info('skipping event: \'%s\', unknown sport: \'%s\'', event_name, sport_name)
            continue


        markets = event_markets.get(event_data['ig'], [])

        event = LiveEvent(
            name=event_name,
            buk=BUK,
            date=f'{event_data["gsd"]}T{event_data["gst"]}Z',
            score=event_data['gso'],
            sport=sport,
            country=event_data['orn'],
            competition=event_data['ln'],
            open_market_count=-1,
            markets=markets,
        )

        events.append(event)
    
    logger.info('SUCCESS got %d live events', len(events))
    return events
