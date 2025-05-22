from dataclasses import dataclass, field
from datetime import timedelta, datetime

from geometry import Point, get_distance
from ns import Stop


@dataclass
class Result:
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
