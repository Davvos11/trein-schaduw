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


@dataclass
class JourneyResult:
    name: str
    number: int
    direction: str
    duration: float
    stops: list[Stop]


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

    def get_journey(self, journey_id: int) -> JourneyResult:
        response = self._get_json(
            f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/journey?train={journey_id}&omitCrowdForecast=true")
        stops = response["payload"]["stops"]
        stops_result = []
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
            stops_result.append(Stop(station_code, name, departure, arrival))

        product = stops[0]["departures"][0]["product"]
        info = JourneyResult(
            f"{product['operatorName']} {product['longCategoryName']}",
            journey_id,
            stops[0]["destination"],
            (stops_result[-1].arrival - stops_result[0].departure).total_seconds(),
            stops_result
        )

        return info

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
                leg["origin"].get("plannedTrack") or leg["origin"].get("actualTrack"),
                leg["destination"].get("plannedTrack") or leg["destination"].get("actualTrack"),
                [s["name"] for s in leg["stops"]][1:-1],
            )
            result.append(journey)
        return result

    def get_stations(self) -> list[tuple[str, str]]:
        response = self._get_json("https://gateway.apiportal.ns.nl/nsapp-stations/v3?includeNonPlannableStations=false")
        stations = [(station["id"]["code"], station["names"]["long"]) for station in response["payload"]]

        stations_grouped = dict()
        for code, name in stations:
            group_name = name.split(" ")[0]
            stations_grouped.setdefault(group_name, []).append((code, name))

        stations_sorted = []
        for stations_set in stations_grouped.values():
            sorted_set = sorted(stations_set, key=lambda station: station[1])
            centraal = next(filter(lambda station: "Centraal" in station[1], stations_set), None)
            if centraal is not None:
                sorted_set.remove(centraal)
                stations_sorted.append(centraal)
            stations_sorted.extend(sorted_set)
        return stations_sorted
