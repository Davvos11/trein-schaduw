# Trein schaduw

Aan welke kant van de trein moet ik zitten om in de zon/schaduw te zitten? 

## Setup and usage:
- Copy `.env.dist` to `.env` and set `NS_API_KEY` to your NS API key
  (see https://apiportal.ns.nl/startersguide)
- Make sure [Poetry](https://python-poetry.org/docs/) is installed.
- Run using:
    ```shell
    poetry update # (first time only)
    poetry run python main.py --treinstel [materieelnummer]
    # or 
    poetry run python main.py --rit [ritnummer]
    # To list stations and their codes:
    poetry run python main-stations.py
    # To list trips between two stations
    poetry run python main-search.py --from [station code] --to [station code]
    # Or, launch the web frontend
    poetry run fastapi dev web.py
    ```

## Resultaat:
![Figure_1](https://github.com/user-attachments/assets/763c5053-ff34-4e95-9f36-f531ba7e5e14)
