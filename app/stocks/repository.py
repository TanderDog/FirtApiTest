from abc import ABC, abstractmethod
from datetime import date


class TicketsRepository(ABC):

    @abstractmethod
    async def add_raw(self, secid: str, price: float) -> dict:
        ...

    @abstractmethod
    async def add_daily(self, secid: str, price: float, target_date: date | None = None) -> None:
        ...

    @abstractmethod
    async def get_raw(self, secid: str, target_date: date | None = None, limit: int = 1) -> list[dict]:
        ...

    @abstractmethod
    async def get_daily(self, secid: str, target_date: date) -> float | None:
        ...

    @abstractmethod
    async def get_daily_paginated(self, page: int, size: int) -> dict:
        ...

    @abstractmethod
    async def get_price_avg(self, secid: str, days: int = 7) -> float | None:
        ...

    @abstractmethod
    async def get_price_volatility(self, secid: str, days: int = 7) -> float | None:
        ...
