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

    def time_string(self) -> str:
        dep_str = arr_str = None
        if self.departure is not None:
            dep_str = self.departure.strftime('%H:%M')
        if self.arrival is not None:
            arr_str = self.arrival.strftime('%H:%M')
        show_both = dep_str is not None and arr_str is not None and dep_str != arr_str

        if show_both:
            return f"{arr_str} - {dep_str}"
        elif dep_str is not None:
            return dep_str
        elif arr_str is not None:
            return arr_str
        else:
            return ''


@dataclass
class Journey:
    name: str
    number: int
    direction: str
    departure: datetime
    arrival: datetime
    dep_track: str
    arr_track: str
    stops: list[str]


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

    def get_from_stations(self, from_station: str, to_station: str, timestamp: Optional[datetime] = None) \
            -> list[Journey]:
        url = (f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips"
               f"?fromStation={from_station}&toStation={to_station}"
               f"&entireTripModality=train")
        if timestamp is not None:
            url += f"&dateTime={timestamp.strftime('%Y-%m-%dT%H:%M:%S')}"
        response = self._get_json(url)
        trips = response["trips"]

        result = []
        for trip in trips:
            if trip["transfers"] > 0:
                continue
            leg = trip["legs"][0]
            journey = Journey(
                leg["product"]["displayName"],
                int(leg["product"]["number"]),
                leg["direction"],
                datetime.fromisoformat(leg["origin"]["plannedDateTime"]),
                datetime.fromisoformat(leg["destination"]["plannedDateTime"]),
                leg["origin"]["plannedTrack"],  # TODO actualtrack
                leg["destination"]["plannedTrack"],
                [s["name"] for s in leg["stops"]][1:-1],
            )
            result.append(journey)
        return result

    def get_stations(self) -> list[tuple[str, str]]:
        response = self._get_json("https://gateway.apiportal.ns.nl/nsapp-stations/v3?includeNonPlannableStations=false")
        return [(station["id"]["code"], station["names"]["long"]) for station in response["payload"]]
