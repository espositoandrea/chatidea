FROM --platform=linux/amd64 python:3.9.6 AS base
LABEL authors="Andrea Esposito"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

FROM base AS builder
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

ENV POETRY_HOME /opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.4.2
RUN python -m venv /venv

COPY pyproject.toml poetry.lock README.md ./
RUN $POETRY_HOME/bin/poetry config virtualenvs.in-project true && \
    $POETRY_HOME/bin/poetry install --only=main --no-root

COPY chatidea chatidea
RUN $POETRY_HOME/bin/poetry build

FROM base as final

RUN apt-get update && apt-get install -y unixodbc curl gnupg
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl -sSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18
COPY --from=builder /venv /venv
COPY --from=builder /usr/src/app/dist .
COPY .env resources ./
RUN . /venv/bin/activate
RUN pip install *.whl

CMD ["python3", "-m", "chatidea"]