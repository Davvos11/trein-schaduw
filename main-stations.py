from argparse import ArgumentParser

from ns import NS


def main() -> None:
    ns = NS()
    stations = ns.get_stations()
    for code, name in stations:
        print(f"{code}: {name}")


if __name__ == '__main__':
    arg_parser = ArgumentParser(description="Vind stations")

    args = arg_parser.parse_args()

    main()
