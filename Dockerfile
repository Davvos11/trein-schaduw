FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1

RUN pip install poetry>=2.0.1

WORKDIR /code
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false \
    && poetry update --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["uvicorn", "web:app"]