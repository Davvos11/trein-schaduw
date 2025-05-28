import time
from argparse import ArgumentParser
from dataclasses import dataclass, asdict
from datetime import timedelta
from typing import Optional

from sun_position_calculator import SunPositionCalculator

from geometry import Vec
from logic import collect_segments, collect_distances, SegmentResult, Result, collect_bearings, filter_stops
from ns import NS, JourneyResult
from plot import Plot


def main(journey_id: Optional[int], train_nr: Optional[int],
         from_station: Optional[str] = None, to_station: Optional[str] = None,
         show_list: bool = False) -> None:
    t = time.time()
    ns = NS()
    result = get_result(ns, journey_id, train_nr, from_station, to_station, show_list)
    print(f"Time: {time.time() - t:.2f}s")

    if not show_list:
        plot = Plot()
        plot.add_results(result.result)
        plot.show()

@dataclass
class FinalResult(JourneyResult):
    result: list[Result]
    left: float
    right: float

def get_result(ns: NS, journey_id: Optional[int], train_nr: Optional[int],
               from_station: Optional[str] = None, to_station: Optional[str] = None,
               show_list: bool = False) -> FinalResult:
    assert train_nr is not None or journey_id is not None, "Provide either journey_id or train_nr"
    assert not (train_nr is not None and journey_id is not None), "Provide either journey_id or train_nr"

    calculator = SunPositionCalculator()
    if journey_id is None:
        journey_id = ns.get_journey_id(train_nr)
        print(f"Got journey {journey_id} from train {train_nr}")
    journey = ns.get_journey(journey_id)

    stops = filter_stops(journey.stops, from_station, to_station)

    if show_list:
        for stop in stops:
            print(f"{stop.code}: {stop.name} ({stop.time_string()})")
        return FinalResult(**asdict(journey), result=[])

    result = []
    duration_left = 0
    duration_right = 0

    segments = collect_segments(stops)
    previous_bearing = None
    made_kop = False
    for segment in segments:
        segment_result = []
        kop = False

        stop_ids = [s.code for s in segment.get_stops()]
        route = ns.get_route(stop_ids)
        total_distance, distances = collect_distances(route)
        speed = total_distance / segment.duration.total_seconds()
        # print(f"{segment.stop1.departure.time()} {segment.stop1.name} - {segment.stop2.name}:"
        #       f" {total_distance / 1000:.2f} km, {segment.duration}, {speed:.2f} m/s, {speed * 3.6:.2f} km/h")

        current_time = segment.stop1.departure

        line_segments, start_bearing, end_bearing = collect_bearings(route, distances)
        if (previous_bearing is not None and
                2.95 < abs(previous_bearing - start_bearing) < 3.5):
            # Save that we made kop at this segment for visualisation
            kop = True
            # Flip the `made_kop` variable so we can flip left and right accordingly
            made_kop = not made_kop
        previous_bearing = end_bearing

        for line in line_segments:
            train_vector = Vec.from_bearing(line.bearing_avg())
            train_vector_left = train_vector.rotate_left()
            train_vector_right = train_vector.rotate_right()

            sun_position = calculator.pos(current_time.timestamp() * 1000, line.position.lat, line.position.lon)
            # Note: negate / flip 180 degrees because the sun shines in the opposite direction of the azimuth
            sun_vector = -Vec.from_bearing(sun_position.azimuth)

            dot_left = sun_vector.dot(train_vector_left)
            dot_right = sun_vector.dot(train_vector_right)
            if made_kop:
                dot_left, dot_right = dot_right, dot_left
            # print("Sun: {bearing_to_compass(sun_position.azimuth)}, train: {bearing_to_compass(train_bearing)},"
            #       " left: {dot_left}, right: {dot_right}")

            if sun_position.altitude < 0.05:
                multiplier = max(0, sun_position.altitude / 0.05)
                dot_left *= multiplier
                dot_right *= multiplier

            duration = line.distance / speed

            segment_result.append(SegmentResult(current_time, dot_left, dot_right, sun_position.altitude))
            if dot_left > 0:
                duration_left += duration
            if dot_right > 0:
                duration_right += duration

            current_time += timedelta(seconds=duration)
        result.append(Result(segment.stop1.name, segment.stop2.name, kop, segment_result))

    return FinalResult(**asdict(journey), result=result, left=duration_left, right=duration_right)


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Welke kant van de trein heeft meer schaduw?")
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--treinstel", type=int, help="Treinstel number, gets current journey of this train")
    group.add_argument("--rit", type=int, help="Train / journey number, use 'main-search.py' to get this number")
    arg_parser.add_argument("--list", action='store_true',
                            help="List stops of tis journey, use this to get the station codes for --from and --to")
    arg_parser.add_argument("--from", dest="from_", type=str, required=False,
                            help="Departure station code, use --list to get the correct code")
    arg_parser.add_argument("--to", type=str, required=False,
                            help="Arrival station code, use --list to get the correct code")

    args = arg_parser.parse_args()

    main(args.rit, args.treinstel, args.from_, args.to, args.list)
