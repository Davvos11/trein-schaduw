# Trein schaduw

Aan welke kant van de trein moet ik zitten om in de zon/schaduw te zitten? 
(https://trein.dovatvis.nl)

## CLI usage:
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
    ```

## Webserver usage:
- Follow the same steps for setting up Poetry and `NS_API_KEY` as above.
- Set up a Redis server, for example using Docker like so:
  ```shell
  docker run --name redis -p 6379:6379 -d redis
  ```
- Set `REDIS_HOST` correctly in `.env`
- Start the webserver (for development):
  ```shell
  poetry run fastapi dev web
  ```
- Or, build the Dockerfile for deployment.

## Resultaat (CLI):
![Figure_1](https://github.com/user-attachments/assets/763c5053-ff34-4e95-9f36-f531ba7e5e14)

## Resultaat webserver:
See https://trein.dovatvis.nl.
