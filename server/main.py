# await fetch("https://api.etoto.pl/livebetting-api/rest/livebetting/v1/api/running/games/major", {
#     "credentials": "include",
#     "headers": {
#         "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
#         "Accept": "application/json, text/javascript, */*; q=0.01",
#         "Accept-Language": "en-US,en;q=0.5",
#         "Content-Type": "application/json; charset=utf-8",
#         "Request-Language": "pl",
#         "Alt-Used": "api.etoto.pl",
#         "Sec-Fetch-Dest": "empty",
#         "Sec-Fetch-Mode": "cors",
#         "Sec-Fetch-Site": "same-site"
#     },
#     "referrer": "https://www.etoto.pl/",
#     "method": "GET",
#     "mode": "cors"
# });

# GET /livebetting-api/rest/livebetting/v1/api/running/games/major HTTP/3
# Host: api.etoto.pl
# User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0
# Accept: application/json, text/javascript, */*; q=0.01
# Accept-Language: en-US,en;q=0.5
# Accept-Encoding: gzip, deflate, br
# Content-Type: application/json; charset=utf-8
# Request-Language: pl
# Origin: https://www.etoto.pl
# Alt-Used: api.etoto.pl
# Connection: keep-alive
# Referer: https://www.etoto.pl/
# Cookie: cf_clearance=UvmbxHZj29WFvlAWu.BbvdrZsc7D7HBq8Rtgsu4XiSI-1701641615-0-1-c60665bf.40166773.68972252-0.2.1701641615; smvr=eyJ2aXNpdHMiOjEsInZpZXdzIjo0LCJ0cyI6MTcwMTY0NDg1OTkyOCwibnVtYmVyT2ZSZWplY3Rpb25CdXR0b25DbGljayI6MCwiaXNOZXdTZXNzaW9uIjpmYWxzZX0=; smuuid=18c31b5e9e3-fcac50bb81ad-fae812a6-a1f93b5f-aa2e1796-23c27bb769c7; _smvs=SEARCH_ENGINE; lsn=web2; _gcl_au=1.1.1104830623.1701644830; _ga_5S1WXK15TB=GS1.1.1701644830.1.0.1701644830.0.0.0; _ga=GA1.2.672722328.1701644831; _ga_HLPY006X9W=GS1.1.1701644830.1.0.1701644830.60.0.0; _gid=GA1.2.727354823.1701644844; _fbp=fb.1.1701644852907.1186898530
# Sec-Fetch-Dest: empty
# Sec-Fetch-Mode: cors
# Sec-Fetch-Site: same-site
# TE: trailers

# curl 'https://api.etoto.pl/livebetting-api/rest/livebetting/v1/api/running/games/major' --compressed -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Content-Type: application/json; charset=utf-8' -H 'Request-Language: pl' -H 'Origin: https://www.etoto.pl' -H 'Alt-Used: api.etoto.pl' -H 'Connection: keep-alive' -H 'Referer: https://www.etoto.pl/' -H 'Cookie: cf_clearance=UvmbxHZj29WFvlAWu.BbvdrZsc7D7HBq8Rtgsu4XiSI-1701641615-0-1-c60665bf.40166773.68972252-0.2.1701641615; smvr=eyJ2aXNpdHMiOjEsInZpZXdzIjo0LCJ0cyI6MTcwMTY0NDg1OTkyOCwibnVtYmVyT2ZSZWplY3Rpb25CdXR0b25DbGljayI6MCwiaXNOZXdTZXNzaW9uIjpmYWxzZX0=; smuuid=18c31b5e9e3-fcac50bb81ad-fae812a6-a1f93b5f-aa2e1796-23c27bb769c7; _smvs=SEARCH_ENGINE; lsn=web2; _gcl_au=1.1.1104830623.1701644830; _ga_5S1WXK15TB=GS1.1.1701644830.1.0.1701644830.0.0.0; _ga=GA1.2.672722328.1701644831; _ga_HLPY006X9W=GS1.1.1701644830.1.0.1701644830.60.0.0; _gid=GA1.2.727354823.1701644844; _fbp=fb.1.1701644852907.1186898530' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'TE: trailers'
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
import websockets


ETOTO_URL = "https://api.etoto.pl/livebetting-api/rest/livebetting/v1/api/running/games/major"
EFORTUNA_URL = "https://api.efortuna.pl/live3/api/live/matches/overview"
STS_URL = "https://api.sts.pl/web/v1/offer/prematch/popular?to=2023-12-4T14:20&lang=pl"
STS_WS_URL = "wss://live-ws.sts.pl/socket.io/?lang=pl&EIO=3&transport=websocket"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.aclient = httpx.AsyncClient()
    yield
    await app.aclient.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/etoto")
async def get_etoto(req: Request):
    aclient = req.app.aclient
    resp = await aclient.get(ETOTO_URL)
    print(f"\n\n{resp.status_code}\n\n")
    if resp.status_code == 200:
        data = resp.json()["data"]
        # print(f"\n\n{data}\n\n")
        out = []
        for d in (d for d in data if "games" in d):
            print(d["sportName"], d["eventName"])
            x = {
                "sport": d["sportName"],
                "category": d["categoryName"],
                "event": d["eventName"],
                # "score": d["partialScores"],
                "games": [
                    {
                        "name": g["gameName"],
                        "odds": [o["outcomeOdds"] for o in g["outcomes"]],
                    }
                    for g in d["games"]
                ]
            }
            out.append(x)
        return out
    return []


@app.get("/efortuna")
async def get_efortuna(req: Request):
    aclient = req.app.aclient
    resp = await aclient.get(EFORTUNA_URL)
    print(f"\n\n{resp.status_code}\n\n")
    if resp.status_code == 200:
        data = resp.json()
        # print(f"\n\n{data}\n\n")
        out = []
        for sport_data in data:
            sport = sport_data["sport"]
            for league_data in sport_data["leagues"]:
                league = league_data["names"]["pl_PL"]
                for match_data in league_data["matches"]:
                    match = match_data["names"]["pl_PL"]
                    match_dict = {
                        "sport": sport,
                        "league": league,
                        "match": match,
                        "odds": [],
                    }
                    for market_data in match_data["topMarkets"].values():
                        print(market_data)
                        market = market_data["market"]["subNames"]["pl_PL"]
                        market_id = market_data["marketId"]
                        odds_data = market_data["market"]["odds"]
                        odds = [o["value"] for o in odds_data[market_id]]
                        match_dict["odds"].append({ "market": market, "odds": odds })
                    out.append(match_dict) 
        return out
    return []


@app.get("/sts")
async def get_sts(req: Request):


    headers = {
        "X-Api-Key": "5ZU3zqUqo8WjprFgAM",
        "X-Request-UUID": "63952567-e36b-4baf-8dcf-60aa4ea28ea4",
    }
    aclient = req.app.aclient
    resp = await aclient.get(STS_URL, headers=headers)
    print(f"\n\n{resp.status_code}\n\n")
    if resp.status_code == 200:
        data = resp.json()
        # print(f"\n\n{data}\n\n")
        return data
        out = []
        for sport_data in data:
            sport = sport_data["sport"]
            for league_data in sport_data["leagues"]:
                league = league_data["names"]["pl_PL"]
                for match_data in league_data["matches"]:
                    match = match_data["names"]["pl_PL"]
                    match_dict = {
                        "sport": sport,
                        "league": league,
                        "match": match,
                        "odds": [],
                    }
                    for market_data in match_data["topMarkets"].values():
                        print(market_data)
                        market = market_data["market"]["subNames"]["pl_PL"]
                        market_id = market_data["marketId"]
                        odds_data = market_data["market"]["odds"]
                        odds = [o["value"] for o in odds_data[market_id]]
                        match_dict["odds"].append({ "market": market, "odds": odds })
                    out.append(match_dict) 
        return out
    return []

    

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    print(f"client id: {client_id}")
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws/1");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)


# GET /web/v1/offer/prematch/popular?to=2023-12-11T12:00&lang=pl HTTP/3
# Host: api.sts.pl
# User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0
# Accept: application/json, text/plain, */*
# Accept-Language: en-US,en;q=0.5
# Accept-Encoding: gzip, deflate, br
# Content-Type: application/json
# X-Api-Key: 5ZU3zqUqo8WjprFgAM
# X-Request-UUID: 63952567-e36b-4baf-8dcf-60aa4ea28ea4
# X-Platform: desktop-rwd
# Origin: https://www.sts.pl
# Alt-Used: api.sts.pl
# Connection: keep-alive
# Referer: https://www.sts.pl/
# Cookie: registration_version=B.1; __cfruid=3e9e4b39ac540ee828134c300a0ee5d9069ab23b-1701693935; cf_clearance=7_l3W00JVOwS3RSsO2C7jkoKh7av44VTswCD4IMd2xI-1701694007-0-1-c60665bf.40166773.68972252-0.2.1701694007; campaign=PewneSTS; entry_url=https%3A%2F%2Fwww.sts.pl%2F; welcome_screen=0.0.3-yes; marketing_attribution_history=%5B%7B%22timestamp%22%3A1701694360981%2C%22referrer%22%3A%22%22%2C%22attributes%22%3A%5B%5D%7D%2C%7B%22timestamp%22%3A1701694286795%2C%22referrer%22%3A%22%22%2C%22attributes%22%3A%5B%5D%7D%2C%7B%22timestamp%22%3A1701694009787%2C%22referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22attributes%22%3A%5B%5D%7D%5D; cpws_at=ARgIcHEViTAbLardOrmICUrA; promoCode=PewneSTS
# Sec-Fetch-Dest: empty
# Sec-Fetch-Mode: cors
# Sec-Fetch-Site: same-site
# If-Modified-Since: Mon, 04 Dec 2023 12:56:38 GMT
# TE: trailers