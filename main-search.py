from argparse import ArgumentParser
from datetime import datetime, time
from typing import Optional

from ns import NS


def main(from_station: str, to_station: str, dep_time: Optional[time] = None) -> None:
    ns = NS()
    if dep_time is not None:
        dep_timestamp = datetime.today()
        dep_timestamp = dep_timestamp.replace(hour=dep_time.hour, minute=dep_time.minute, second=0, microsecond=0)
    else:
        dep_timestamp = None
    journeys = ns.get_from_stations(from_station, to_station, dep_timestamp)
    for journey in journeys:
        print(
            f"{journey.departure.strftime('%H:%M')} spoor {journey.dep_track}: {journey.name} naar {journey.direction}"
            f" ({journey.number})\n"
            f"\t via {', '.join(journey.stops)}\n"
            f"\t aankomst op spoor {journey.arr_track} om {journey.arrival.strftime('%H:%M')}")


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Vind treinrit")
    arg_parser.add_argument("--from", dest="from_", type=str, help="Departure station code")
    arg_parser.add_argument("--to", type=str, help="Arrival station code")
    arg_parser.add_argument("--time", type=lambda s: datetime.strptime(s, "%H:%M").time(),
                            help="Departure time (hh:mm)",
                            required=False)

    args = arg_parser.parse_args()

    main(args.from_, args.to, args.time)
