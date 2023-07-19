import distutils.util
import json
import logging
import os
import pathlib
from typing import Literal, Union, Any, Type

import dotenv
import yaml
from pydantic import parse_obj_as
from pypika import Query, MSSQLQuery, MySQLQuery, SQLLiteQuery, PostgreSQLQuery, OracleQuery, RedshiftQuery, \
    ClickHouseQuery
from pypika.enums import Dialects

from .config import *

env = dotenv.dotenv_values(dotenv.find_dotenv(usecwd=True))
file_path = pathlib.Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)
CONFIG_TYPES = Literal["concept", "concept_s", "view", "schema"]


def get_db_dialect() -> Type[Query]:
    dialect = [e for e in Dialects if e.value == env.get("DB_DIALECT", "mysql")]
    if not dialect:
        raise ValueError(f'Unrecognized dialect: {env.get("DB_DIALECT", "mysql")}')

    dialect_to_obj: dict[Dialects, Type[Query]] = {
        Dialects.MSSQL: MSSQLQuery,
        Dialects.MYSQL: MySQLQuery,
        Dialects.SQLLITE: SQLLiteQuery,
        Dialects.POSTGRESQL: PostgreSQLQuery,
        Dialects.ORACLE: OracleQuery,
        Dialects.REDSHIFT: RedshiftQuery,
        Dialects.CLICKHOUSE: ClickHouseQuery
    }
    return dialect_to_obj.get(dialect[0], Query)


def get_db_config(config_type: CONFIG_TYPES) -> \
        Union[dict[str, Any], list[dict[str, Any]]]:
    DB_RESOURCES_PATH = pathlib.Path(
        file_path / env.get("DB_RESOURCES_PATH")) or file_path / 'resources' / 'db'
    file_name = env.get(f'DB_{config_type.upper()}_PATH',
                        f'db_{config_type}_{DB_NAME}.json')
    path = DB_RESOURCES_PATH / file_name
    logger.info('Database %s file: %s', config_type, path)
    logger.info('Loading database %s file...', config_type)
    with path.open("r") as f:
        config = json.load(f) if path.suffix == ".json" else yaml.safe_load(f)
    logger.info('Database %s file has been loaded!', config_type)
    return config


IS_DEBUG = distutils.util.strtobool(env.get("DEBUG", "False"))
# selector

DB_DRIVER = env['DB_DRIVER']
DB_USER = env['DB_USER']
DB_PASSWORD = env.get('DB_PASSWORD')
DB_HOST = env['DB_HOST']
DB_NAME = env['DB_NAME']
DB_CHARSET = env.get("DB_CHARSET")
DialectQuery: Type[Query] = get_db_dialect()

NLU_API_ENDPOINT = env.get("NLU_API_ENDPOINT", "http://localhost:5005")
# files

LOG_DIR_PATH_AND_SEP = file_path / 'logs'
NLU_DATA_PATH = file_path / 'writer' / 'rasa_dataset_training.json'
NLU_MODEL_PATH = file_path / 'models' / 'nlu_model.tar.gz'
NLU_MODEL_DIR_PATH = NLU_MODEL_PATH.parent

DB_VIEW = parse_obj_as(DatabaseView, get_db_config('view'))
DB_CONCEPT = parse_obj_as(DatabaseConcepts, get_db_config('concept'))
DB_CONCEPT_S = get_db_config("concept_s")
DB_SCHEMA = parse_obj_as(DatabaseSchema, get_db_config("schema"))

CHATITO_TEMPLATE_PATH = file_path / 'writer' / 'chatito_template.chatito'
CHATITO_MODEL_PATH = file_path / 'writer' / 'chatito_model.chatito'

# settings

TOKEN_TELEGRAM = env['TELEGRAM_TOKEN']

INTENT_CONFIDENCE_THRESHOLD = 0.4
ELEMENT_SIMILARITY_DISTANCE_THRESHOLD = 3  # 5 o 3?
ELEMENT_VISU_LIMIT = 5
CONTEXT_VISU_LIMIT = 4

CONTEXT_PERSISTENCE_SECONDS = 5 * 60
CONTEXT_MAX_LENGTH = 16

QUERY_LIMIT = 100  # 0 for no limit

# db

remote = True if os.environ.get('PYTHONANYWHERE_SITE') else False

# nlu

NLU_CONFIG_PIPELINE = "supervised_embeddings"  # "spacy_sklearn"
NLU_CONFIG_LANGUAGE = "en"
