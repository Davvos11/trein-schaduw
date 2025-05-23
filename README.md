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
    ```

## Resultaat:
![Figure_1](https://github.com/user-attachments/assets/763c5053-ff34-4e95-9f36-f531ba7e5e14)
