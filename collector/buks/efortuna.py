import logging
from bs4 import BeautifulSoup
import httpx
import asyncio
from pprint import pprint

from models import PrematchEvent, LiveEvent, Market, Odd, Buk

from utils import batched


logger = logging.getLogger(__name__)


BUK_NAME = 'efortuna'
BUK_URL = 'https://www.efortuna.pl'
LIVE_URL = 'https://api.efortuna.pl/live3/api/live/matches/overview'
# /ajax/zaklady-bukmacherskie/tenis/k-australian-open-singiel-kwalifikacje?type=all&timeTo=&rateFrom=&rateTo=
# https://www.efortuna.pl/ajax/zaklady-bukmacherskie/tenis/k-australian-open-singiel-kwalifikacje?type=all&timeTo=&rateFrom=&rateTo=


async def get_efortuna_prematch(c: httpx.AsyncClient) -> list[PrematchEvent]:
    logger.info('TRY get efortuna prematch events')
    resp = await c.get(BUK_URL)

    if resp.status_code != 200:
        return []

    efortuna_html = resp.text
    soup = BeautifulSoup(efortuna_html, 'html.parser') 
    sport_tree_as = soup.select('#filterbox-ref-sport-tree > li.item-sport > a.btn-sport')
    sports = []
    for a in sport_tree_as:
        span = a.select_one('span.sport-name')
        if span is None:
            continue
        sport_link = a['href']
        sport_name = span.text.strip()
        sports.append((sport_name, sport_link))

    events = []
    buk = Buk(name=BUK_NAME, url=BUK_URL)
    for sport_name, sport_link in sports:
        resp = await c.get(f'{BUK_URL}{sport_link}')

        if resp.status_code != 200:
            continue        

        sport_html = resp.text
        soup = BeautifulSoup(sport_html, 'html.parser')
        sport_events_sections = soup.select('#sport-events-list-content > section.competition-box')
        for competion_section in sport_events_sections:
            sport_name = competion_section.select_one('span.sport-name').text.strip()
            competition_name = competion_section.select_one('span.competition-name').text.strip()
            event_list = competion_section.select_one('.events-list')
            
            submarket_col = event_list.select_one('thead .col-title > span.market-sub-name').text.strip()
            odds_cols = [odds_col.text.strip() for odds_col in event_list.select('thead .col-odds > .odds-name')]
            submarket_names = [submarket_name['data-value'].strip() for submarket_name in event_list.select('tbody .col-title')]
            odds = [odds_value.text.strip() for odds_value in event_list.select('tbody .col-odds .odds-value')]
            dates = [date.text.strip() for date in event_list.select('tbody .col-date .event-datetime')]
            for event_name, event_date, event_markets in zip(submarket_names, dates, batched(odds, len(odds_cols))):
                event = PrematchEvent(
                    name=event_name,
                    sport=sport_name,
                    competition=competition_name,
                    country='country',
                    open_market_count=111,
                    buk=buk,
                    date=event_date,
                    markets=[
                        {
                            'name': submarket_col,
                            'odds': event_markets,
                        },
                    ],
                )
                # print(submarket_col)
                # pprint(event_markets)
                events.append(event)
            
        await asyncio.sleep(5)
        
    logger.info('SUCCESS get %d efortuna prematch events', len(events))
    return events


async def get_efortuna_live(c: httpx.AsyncClient) -> list[LiveEvent]:
    logger.info('TRY get efortuna live events')
    resp = await c.get(LIVE_URL)
    if resp.status_code != 200:
        return []
    sports_data = resp.json()
    events = []
    for sport_data in sports_data:
        sport = sport_data['sport']
        for league_data in sport_data['leagues']:
            league = league_data['names']['pl_PL']
            for event_data in league_data['matches']:
                match = event_data['names']['pl_PL']
                event = {
                    'sport': sport,
                    'league': league,
                    'match': match,
                    'odds': [],
                }
                for market_data in event_data['topMarkets'].values():
                    market = market_data['market']['subNames']['pl_PL']
                    market_id = market_data['marketId']
                    odds_data = market_data['market']['odds']
                    odds = [o['value'] for o in odds_data[market_id]]
                    event['odds'].append({ 'market': market, 'odds': odds })
                    # print(event)
                events.append(event)
    logger.info('SUCCESS get %d efortuna live events', len(events))
    return events
