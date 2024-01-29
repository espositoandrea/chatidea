# CHATIDEA

CHATIDEA is a framework that allows the generation of a chatbot starting from a
database's schema.

This file holds a brief documentation for the implementation of the CHATIDEA
framework, just enough to get contributors up and running. For a detailed
documentation, please visit [the full documentation](file:///docs). An online
version can be found on [ReadTheDocs](https://chatidea.readthedocs.io/)

## Requirements

This version of CHATIDEA requires the following to be installed in your
machine (please refer to the official documentations for instructions on how to
install them).

- [Rasa](https://rasa.com)
- [Python 3.9 (with PIP)](https://www.python.org/downloads)
- [Node.js (with NPM)](https://nodejs.org/)
- [Pipenv](https://pipenv.pypa.io)
- [Docker and Docker Compose](https://www.docker.com)
- [ODBC drivers](https://github.com/mkleehammer/pyodbc/wiki/Install)

Before continuing, a database is needed. Be sure to have a DBMS running on your
system or on a remote server, and remember to set the appropriate SQL dialect
needed in the file `chatidea/database/broker.py`.

Install all Python and Node.js dependencies in a virtual environment using the
following command:

```shell
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
npm i --dev
```

Then edit the `.env` file to fit your environment. If the `.env` file does not
exist, copy the provided example template. This can be done using the following
command.

```shell
cp .env.example .env
```

## Execute the Pipeline

The NLU pipeline is fully contained in the directory `nlu-model`, thus be sure
to change the directory using the following command before executing the
pipeline.

```shell
cd nlu-model
```

### Generate Data and Train the Model

```shell
dvc repro
```

## Start the Rasa Server

```shell
rasa run --enable-api
```

## Deploying Information

The project is configured to be deployed using containerization. More precisely,
one container for each microservice is expected. Thus, this repository holds
configuration files for Docker, using Dockerfiles and docker-compose (used to
manage the communication between the microservices). To build the deployment
containers, run the following:

```shell
docker-compose build
```

To execute the chatbot, run the following command (remove the `-d` at the end to
avoid executing as a daemon).

```shell
docker-compose up -d
```

To shut down the services, you can either use `C-c` (if you are not running in
daemon mode) or you can run the following command:

```shell
docker-compose down
```

### Testing the Deployment on Apple Silicon and Other ARM Processors

At the moment, the project is based on [Rasa](https://rasa.com). Sadly, the
official Docker image of Rasa does not support the ARM architecture. As a
workaround, until an official version is released,
an [unofficial image](https://hub.docker.com/r/khalosa/rasa-aarch64) can be
downloaded from [Docker Hub](https://hub.docker.com). To use it, in the
file `nlu-model/Dockerfile` replace the `FROM` image by changing `rasa/rasa`
to `khalosa/rasa-aarch64:3.5.2`. The following command does that automatically.

**Note:**
`sed`'s inplace option `-i` is not used to ensure POSIX compatibility, as macOS
systems do not ship by default with the GNU version of `sed`

```shell
TEMP_FILE=$(mktemp) && \
    sed '1s;rasa/rasa;khalosa/rasa-aarch64:3.5.2;' nlu-model/Dockerfile > $TEMP_FILE && \
    mv $TEMP_FILE nlu-model/Dockerfile
```

## Known Issues and Future Actions

-   [ ] Separate NLU model's environment from the main app's environment

