import json
import os
from dataclasses import asdict
from datetime import datetime, date
from typing import Any, Callable, TypeVar, Optional, Type

import redis
from dacite import from_dict
from dotenv import load_dotenv
from typing_extensions import override, ParamSpec

from geometry import Point
from main import get_result, FinalResult
from ns import NS, Journey, JourneyResult

Args = ParamSpec("Args")
T = TypeVar("T")

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def json_deserial(dct):
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                # Attempt to parse ISO datetime strings
                dct[key] = datetime.fromisoformat(value)
            except ValueError:
                pass  # Leave value as-is if it's not a valid ISO format
    return dct


class Cache:
    def __init__(self):
        load_dotenv()
        host = os.getenv("REDIS_HOST", "")
        self._redis = redis.Redis(host=host)

    def get(self, key: str) -> Optional[Any]:
        value = self._redis.get(key)
        if value is None:
            return None
        return json.loads(value, object_hook=json_deserial)

    def set(self, key: str, value: Any, expiration: int):
        self._redis.set(key, json.dumps(value, default=json_serial), ex=expiration)

    def set_dataclass(self, key: str, value: Any, expiration: int):
        if isinstance(value, list):
            value = [asdict(item) for item in value]
        else:
            value = asdict(value)
        self.set(key, value, expiration)

    def cached(self, key: str, expiration: int, data_type: Optional[Type[T]], fn: Callable[Args, T],
               *args: Args.args, **kwargs: Args.kwargs) -> T:
        if (cached := self.get(key)) is not None:
            if data_type is not None:
                return from_dict(data_class=data_type, data=cached)
            else:
                return cached
        result = fn(*args, **kwargs)
        if data_type is not None:
            self.set_dataclass(key, result, expiration)
        else:
            self.set(key, result, expiration)
        return result

    def cached_list(self, key: str, expiration: int, list_type: Optional[Type[T]], fn: Callable[Args, list[T]],
                    *args: Args.args, **kwargs: Args.kwargs) -> list[T]:
        if (cached := self.get(key)) is not None:
            if list_type is not None:
                return [from_dict(data_class=list_type, data=item) for item in cached]
            else:
                return cached
        result = fn(*args, **kwargs)
        if list_type is not None:
            self.set_dataclass(key, result, expiration)
        else:
            self.set(key, result, expiration)
        return result


class NsCached(NS):
    def __init__(self):
        super().__init__()
        self._cache = Cache()

    @override
    def get_journey(self, journey_id: int) -> JourneyResult:
        return self._cache.cached(f"journey-{journey_id}", HOUR, JourneyResult, super().get_journey, journey_id)

    @override
    def get_route(self, station_codes: list[str]) -> list[Point]:
        return self._cache.cached_list("route-" + "-".join(station_codes), DAY, Point, super().get_route, station_codes)

    @override
    def get_from_stations(self, from_station: str, to_station: str, timestamp: Optional[datetime] = None) \
            -> list[Journey]:
        cache_timestamp = (timestamp or datetime.now()).timestamp()
        return self._cache.cached_list(
            f"journeys-{from_station}-{to_station}-{cache_timestamp / 60:.0f}", MINUTE,
            Journey,
            super().get_from_stations, from_station, to_station, timestamp
        )

    @override
    def get_stations(self) -> list[tuple[str, str]]:
        return self._cache.cached_list("stations", DAY, None, super().get_stations)


    def get_result(self, journey_id: Optional[int], train_nr: Optional[int],
                   from_station: Optional[str] = None, to_station: Optional[str] = None) -> FinalResult:
        return self._cache.cached(
            f"result-{journey_id}-{train_nr}-{from_station}-{to_station}", MINUTE, FinalResult,
            get_result, self, journey_id, train_nr, from_station, to_station, False
        )