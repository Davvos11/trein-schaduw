FROM python:3.13-slim@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc

RUN pip install poetry>=2.0.1

WORKDIR /code
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false \
    && poetry update --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["uvicorn", "web:app"]