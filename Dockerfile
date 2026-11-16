FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS build

RUN pip install --no-cache-dir "poetry>=2.0.1"

WORKDIR /code
COPY pyproject.toml poetry.lock ./

# Install the locked dependencies into /code/.venv, without pip in that venv
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true
RUN poetry install --only main --no-root --no-interaction --no-ansi

FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

# Debian fixes not yet in the base image (zlib1g). The app doesn't use pip at runtime,
# and scanners flag the packages pip vendors.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall -y pip

WORKDIR /code
COPY --from=build /code/.venv /code/.venv
ENV PATH="/code/.venv/bin:$PATH"

COPY . .

ENTRYPOINT ["uvicorn", "web:app"]
