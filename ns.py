import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

from geometry import Point


@dataclass
class Stop:
    code: str
    name: str
    departure: Optional[datetime]
    arrival: Optional[datetime]


class NS:
    def __init__(self):
        load_dotenv()
        self.API_KEY = os.getenv("NS_API_KEY", "")

    def _get(self, url: str):
        return requests.get(url, headers={'Cache-Control': 'no-cache', 'Ocp-Apim-Subscription-Key': self.API_KEY})

    def _get_json(self, url: str):
        return self._get(url).json()

    def _get_text(self, url: str):
        return self._get(url).text

    def get_journey_id(self, train_nr: int) -> int:
        journey_id = self._get_text(f"https://gateway.apiportal.ns.nl/virtual-train-api/v1/ritnummer/{train_nr}")
        return int(journey_id)

    def get_stops(self, journey_id: int) -> list[Stop]:
        response = self._get_json(
            f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/journey?train={journey_id}&omitCrowdForecast=true")
        stops = response["payload"]["stops"]
        result = []
        for stop in stops:
            station_code = stop["id"].split("_")[0]
            name = stop["stop"]["name"]
            departures = stop["departures"]
            departure = None
            if len(departures) > 0:
                assert len(departures) == 1
                departure = departures[0]["plannedTime"]
                departure = datetime.fromisoformat(departure)
            arrivals = stop["arrivals"]
            arrival = None
            if len(arrivals) > 0:
                assert len(arrivals) == 1
                arrival = arrivals[0]["plannedTime"]
                arrival = datetime.fromisoformat(arrival)
            result.append(Stop(station_code, name, departure, arrival))
        return result

    def get_route(self, station_codes: list[str]) -> list[Point]:
        station_str = ",".join(station_codes)
        response = self._get_json(
            f"https://gateway.apiportal.ns.nl/Spoorkaart-API/api/v1/traject.json?stations={station_str}")
        # print(json.dumps(response["payload"]))
        # print()
        features = response["payload"]["features"]
        assert len(features) == 1
        coordinates = features[0]["geometry"]["coordinates"]
        return [Point.from_geojson(c) for c in coordinates]
