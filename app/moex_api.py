import httpx
import asyncio

async def fetch_one(client: httpx.AsyncClient, ticker: str):
    url = (
        "https://iss.moex.com/iss/engines/stock/markets/shares"
        f"/securities/{ticker}.json"
        "?iss.meta=off&iss.only=securities,marketdata"
        "&securities.columns=SECID,BOARDID,PREVPRICE"
        "&marketdata.columns=SECID,BOARDID,LAST"
)
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()

    prev_price = None
    for row in data["securities"]["data"]:
        secid, boardid, prevprice = row
        if boardid == "TQBR":
            prev_price = prevprice
            break

    last = None
    for row in data["marketdata"]["data"]:
        secid, boardid, l = row
        if boardid == "TQBR" and l is not None:
            last = l
            break

    return ticker, last, prev_price


async def fetch_prices(tickers: list[str]):
    async with httpx.AsyncClient(timeout=10) as client:
        results = await asyncio.gather(*(fetch_one(client, t) for t in tickers))
    return {ticker: (last, prev_price) for ticker, last, prev_price in results if last is not None}