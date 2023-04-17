import os
import pathlib

file_path = pathlib.Path(__file__).resolve().parent

# selector

select = 'deib'

select_dict = {
    'teachers': [
        'b',
        'teachers',
        '797397572:AAEV1MfR28lTzPsom_2qO2-goJSCKzQZ5d0'
    ],
    'classicmodels': [
        'c',
        'classicmodels',
        '710759393:AAGcrq2gkBd84qa-apwS9quMd5QK0knfWTM'
    ],
    'deib': [
        'd',
        'deib',
        '1046778538:AAF2CKzjxwzCu9fiDLgadBujYKuBKhgKmdE'
    ]
}

abc = select_dict[select][0]
db_name = select_dict[select][1]

# files

LOG_DIR_PATH_AND_SEP = file_path / 'logs'
NLU_DATA_PATH = file_path / 'writer' / 'rasa_dataset_training.json'
NLU_MODEL_PATH = file_path / 'resources' / 'nlu' / 'models' / 'nlu_model'
NLU_MODEL_DIR_PATH = file_path / 'resources' / 'nlu' / 'models'
DB_CONCEPT_PATH = file_path / 'resources' / 'db' / f'db_concept_{abc}.json'
DB_CONCEPT_PATH_S = file_path / 'resources' / 'db' / f'db_concept_s_{abc}.json'
DB_SCHEMA_PATH = file_path / 'resources' / 'db' / f'db_schema_{abc}.json'
DB_VIEW_PATH = file_path / 'resources' / 'db' / f'db_view_{abc}.json'

CHATITO_TEMPLATE_PATH = file_path / 'writer' / 'chatito_template.chatito'
CHATITO_MODEL_PATH = file_path / 'writer' / 'chatito_model.chatito'

# settings

TOKEN_TELEGRAM = select_dict[select][2]

INTENT_CONFIDENCE_THRESHOLD = 0.4
ELEMENT_SIMILARITY_DISTANCE_THRESHOLD = 3  # 5 o 3?
ELEMENT_VISU_LIMIT = 5
CONTEXT_VISU_LIMIT = 4

CONTEXT_PERSISTENCE_SECONDS = 5 * 60
CONTEXT_MAX_LENGTH = 16

QUERY_LIMIT = 100  # 0 for no limit

# db

remote = True if os.environ.get('PYTHONANYWHERE_SITE') else False

DATABASE_USER = 'nicolacastaldo' if remote else 'root'
DATABASE_PASSWORD = 'dataexplorerbot' if remote else ''
DATABASE_HOST = 'nicolacastaldo.mysql.pythonanywhere-services.com' if remote else 'localhost'
DATABASE_NAME = 'nicolacastaldo$classicmodels' if remote else db_name

# nlu

NLU_CONFIG_PIPELINE = "supervised_embeddings"  # "spacy_sklearn"
NLU_CONFIG_LANGUAGE = "en"
