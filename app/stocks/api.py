import httpx
import asyncio


class MoexApiError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def fetch_one(client: httpx.AsyncClient, ticker: str):
    url = (
        "https://iss.moex.com/iss/engines/stock/markets/shares"
        f"/securities/{ticker}.json"
        "?iss.meta=off&iss.only=securities,marketdata"
        "&securities.columns=SECID,BOARDID,PREVPRICE"
        "&marketdata.columns=SECID,BOARDID,LAST"
    )

    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise MoexApiError(
            f"MOEX вернул ошибку для {ticker}: {exc.response.status_code}",
            status_code=exc.response.status_code,
        ) from exc
    except httpx.RequestError as exc:
        raise MoexApiError(f"MOEX недоступен для {ticker}: {exc}") from exc

    data = response.json()

    prev_price = None
    for row in data["securities"]["data"]:
        secid, boardid, prevprice = row
        if boardid == "TQBR":
            prev_price = prevprice
            break

    last = None
    for row in data["marketdata"]["data"]:
        secid, boardid, last_price = row
        if boardid == "TQBR" and last_price is not None:
            last = last_price
            break

    return ticker, last, prev_price


async def fetch_prices(tickers: list[str]):
    async with httpx.AsyncClient(timeout=10) as client:
        results = await asyncio.gather(
            *(fetch_one(client, t) for t in tickers),
            return_exceptions=True,
        )

    prices = {}
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            continue
        _, last, prev_price = result
        if last is not None:
            prices[ticker] = (last, prev_price)

    return prices
