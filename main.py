from argparse import ArgumentParser
from datetime import timedelta
from typing import Optional

from sun_position_calculator import SunPositionCalculator

from geometry import get_bearing, Vec
from logic import collect_segments, collect_distances, Result
from ns import NS
from plot import Plot


def main(journey_id: Optional[int], train_nr: Optional[int]) -> None:
    assert train_nr is not None or journey_id is not None, "Provide either journey_id or train_nr"
    assert not (train_nr is not None and journey_id is not None), "Provide either journey_id or train_nr"

    ns = NS()
    calculator = SunPositionCalculator()
    if journey_id is None:
        journey_id = ns.get_journey_id(train_nr)
        print(f"Got journey {journey_id} from train {train_nr}")
    stops = ns.get_stops(journey_id)

    result = []

    segments = collect_segments(stops)
    for segment in segments:
        segment_result = []

        stop_ids = [s.code for s in segment.get_stops()]
        route = ns.get_route(stop_ids)
        total_distance, distances = collect_distances(route)
        speed = total_distance / segment.duration.total_seconds()
        # print(f"{segment.stop1.departure.time()} {segment.stop1.name} - {segment.stop2.name}:"
        #       f" {total_distance / 1000:.2f} km, {segment.duration}, {speed:.2f} m/s, {speed * 3.6:.2f} km/h")

        current_time = segment.stop1.departure
        # Array for moving average
        train_bearings = []

        for p1, p2, distance in zip(route, route[1:], distances):
            new_train_bearing = get_bearing(p1, p2)
            # Calculate moving average
            if len(train_bearings) == 0:
                train_bearings = [new_train_bearing] * 50
            else:
                train_bearings.pop(0)
                train_bearings.append(new_train_bearing)
            train_bearing = sum(train_bearings) / len(train_bearings)

            train_vector = Vec.from_bearing(train_bearing)
            train_vector_left = train_vector.rotate_left()
            train_vector_right = train_vector.rotate_right()

            sun_position = calculator.pos(current_time.timestamp() * 1000, p1.lat, p1.lon)
            # Note: negate / flip 180 degrees because the sun shines in the opposite direction of the azimuth
            sun_vector = -Vec.from_bearing(sun_position.azimuth)

            dot_left = sun_vector.dot(train_vector_left)
            dot_right = sun_vector.dot(train_vector_right)
            # print("Sun: {bearing_to_compass(sun_position.azimuth)}, train: {bearing_to_compass(train_bearing)},"
            #       " left: {dot_left}, right: {dot_right}")

            segment_result.append(Result(current_time, dot_left, dot_right, sun_position.altitude))

            current_time += timedelta(seconds=distance / speed)
        result.append((segment.stop1.name, segment.stop2.name, segment_result))

    plot = Plot()
    plot.add_results(result)
    plot.show()


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Welke kant van de trein heeft meer schaduw?")
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--treinstel", type=int)
    group.add_argument("--rit", type=int)

    args = arg_parser.parse_args()

    main(args.rit, args.treinstel)
