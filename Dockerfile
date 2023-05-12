FROM python:3.9.6
LABEL authors="Andrea Esposito"
RUN python3 -m pip install pipenv
RUN apt-get update && apt-get install -y unixodbc

RUN apt-get install -y curl gnupg && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl -sSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18

WORKDIR /usr/src/app

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --deploy --system

COPY chatidea chatidea
COPY resources resources
COPY .env .


CMD ["python3", "-m", "chatidea"]