FROM python:3.15-slim@sha256:94d3426f1def7db4a106a232ac121bfd975393e5dfd40a619b955fae45fe7913

RUN pip install poetry>=2.0.1

WORKDIR /code
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false \
    && poetry update --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["uvicorn", "web:app"]