# CHATIDEA's NLU Model

This directory holds the scripts and configuration files for the Natural Language Understanding model used by CHATIDEA.

## Running the Training

Open a shell in this directory (the `nlu-model` directory) and execute `poetry run dvc repro`. Please be sure that the dependencies identified in `dvc.yaml` match the ones you defined in your `.env` file!

## Dependencies Warning

All dependencies are tracked using Poetry. However, RASA still declares a dependency on Pydantic 1.x. This conflicts
with the dependency of the middleware and config files, as they depend on Pydantic 2.x. Since we empirically found that
for our usage we do not incur into errors using an incompatible version of Pydantic, we keep the dependency out of the
`pyproject.toml` and we need to install it manually: after executing `poetry install`, run the following command.

```shell
poetry run pip install "pydantic~=2.0"
```

### Issues on Apple Silicon

There may be some problems with `pyodbc` until the maintainers do not provide a correctly built image of the library for
Apple Silicon. If you incur in errors after installing `pyodbc`, simply reinstall the library using the following
command.

```shell
poetry run pip3 install --force-reinstall --no-binary :all: pyodbc
```
