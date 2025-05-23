from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import Optional

from geometry import Point, get_distance, get_bearing
from ns import Stop

MOVING_AVERAGE = 20
KOP_MOVING_AVERAGE = 3

def filter_stops(stops: list[Stop], from_station: Optional[str], to_station: Optional[str]) -> list[Stop]:
    from_i = 0
    to_i = 0
    if from_station is not None:
        for stop in stops:
            if stop.code != from_station:
                from_i += 1
            else:
                break
    if to_station is not None:
        for stop in stops:
            if stop.code != to_station:
                to_i += 1
            else:
                break
    else:
        to_i = len(stops)
    return stops[from_i:to_i + 1]

@dataclass
class Result:
    stop1: str
    stop2: str
    kop: bool
    items: list['SegmentResult']


@dataclass
class SegmentResult:
    time: datetime
    left: float
    right: float
    altitude: float


@dataclass
class TripSegment:
    stop1: Stop
    stop2: Stop
    intermediate: list[Stop]
    duration: timedelta = field(init=False)

    def __post_init__(self):
        assert self.stop1.departure is not None
        assert self.stop2.arrival is not None
        self.duration = self.stop2.arrival - self.stop1.departure

    def get_stops(self) -> list[Stop]:
        return [self.stop1, *self.intermediate, self.stop2]


def collect_segments(stops: list[Stop]) -> list[TripSegment]:
    if len(stops) <= 1:
        return []

    current_stop = stops[0]
    current_time = current_stop.departure
    assert current_time is not None
    intermediate_stops = []

    result = []
    for i, next_stop in enumerate(stops[1:]):
        next_time = next_stop.arrival
        # Loop until we find a stop with an arrival time
        if next_time is not None:
            # Save this segment
            result.append(TripSegment(current_stop, next_stop, intermediate_stops))
            # Unless we are at the end, this stop should also
            # have a departure time and we can continue.
            if i != len(stops) - 2:  # Note: len -2, because we start enumerating at 1
                current_stop = next_stop
                current_time = next_stop.departure
                assert current_time is not None
                intermediate_stops = []
        else:
            # Otherwise, save this intermediate stop
            intermediate_stops.append(next_stop)
    return result


def collect_distances(points: list[Point]) -> tuple[float, list[float]]:
    distances = []
    total = 0
    if len(points) <= 1:
        return total, distances

    for p1, p2 in zip(points, points[1:]):
        distance = get_distance(p1, p2)
        distances.append(distance)
        total += distance

    return total, distances

@dataclass
class LineSegment:
    position: Point
    distance: float
    bearing: float
    bearing_avg_fwd: float
    bearing_avg_bwd: float

    def bearing_avg(self):
        return (self.bearing_avg_fwd + self.bearing_avg_bwd) / 2


def collect_bearings(route: list[Point], distances: list[float]) -> tuple[list[LineSegment], float, float]:
    results = []

    bearings_forward = []
    for p1, p2, distance in zip(route, route[1:], distances):
        bearing = get_bearing(p1, p2)
        if len(bearings_forward) == 0:
            bearings_forward = [bearing] * MOVING_AVERAGE
        else:
            bearings_forward.pop(0)
            bearings_forward.append(bearing)
        # Calculate moving average
        bearing_avg_fwd = sum(bearings_forward) / len(bearings_forward)
        results.append(LineSegment(p1, distance, bearing, bearing_avg_fwd, 0))

    bearings_backward = []
    for i in reversed(range(len(results))):
        bearing = results[i].bearing
        if len(bearings_backward) == 0:
            bearings_backward = [bearing] * MOVING_AVERAGE
        else:
            bearings_backward.pop(0)
            bearings_backward.append(bearing)
        # Calculate moving average
        bearing_avg_bwd = sum(bearings_backward) / len(bearings_backward)
        results[i].bearing_avg_bwd = bearing_avg_bwd

    # Get small moving average for first and last part of route
    # used to calculate "kop maken"
    window = min(3, len(results))
    avg_start = sum([s.bearing for s in results[:window]]) / window
    avg_end = sum([s.bearing for s in results[-window:]]) / window

    return results, avg_start, avg_end





