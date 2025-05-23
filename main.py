from argparse import ArgumentParser
from datetime import timedelta
from typing import Optional

from sun_position_calculator import SunPositionCalculator

from geometry import Vec
from logic import collect_segments, collect_distances, SegmentResult, Result, collect_bearings
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
                2.95 < previous_bearing - start_bearing < 3.5):
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

            segment_result.append(SegmentResult(current_time, dot_left, dot_right, sun_position.altitude))

            current_time += timedelta(seconds=line.distance / speed)
        result.append(Result(segment.stop1.name, segment.stop2.name, kop, segment_result))

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
