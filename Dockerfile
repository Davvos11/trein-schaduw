FROM python:3.13-slim

RUN pip install poetry>=2.0.1

WORKDIR /code
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false \
    && poetry update --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["uvicorn", "web:app"]