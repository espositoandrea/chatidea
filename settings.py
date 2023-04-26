import os
import pathlib
import dotenv

env = dotenv.dotenv_values()
file_path = pathlib.Path(__file__).resolve().parent

# selector

DB_DRIVER = env['DB_DRIVER']
DB_USER = env['DB_USER']
DB_PASSWORD = env['DB_PASSWORD']
DB_HOST = env['DB_HOST']
DB_NAME = env['DB_NAME']
DB_CHARSET = env["DB_CHARSET"]

NLU_API_ENDPOINT = "http://localhost:5005"
# files

LOG_DIR_PATH_AND_SEP = file_path / 'logs'
NLU_DATA_PATH = file_path / 'writer' / 'rasa_dataset_training.json'
NLU_MODEL_PATH = file_path / 'models' / 'nlu_model.tar.gz'
NLU_MODEL_DIR_PATH = NLU_MODEL_PATH.parent
DB_RESOURCES_PATH = file_path / 'resources' / 'db'
DB_CONCEPT_PATH = DB_RESOURCES_PATH / f'db_concept_{DB_NAME}.json'
DB_CONCEPT_PATH_S = DB_RESOURCES_PATH / f'db_concept_s_{DB_NAME}.json'
DB_SCHEMA_PATH = DB_RESOURCES_PATH / f'db_schema_{DB_NAME}.json'
DB_VIEW_PATH = DB_RESOURCES_PATH / f'db_view_{DB_NAME}.json'

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
