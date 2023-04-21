import dataclasses
import json
import logging
import urllib.parse

import rasa.core.agent
import requests
import re
from rasa.nlu import model as nlu_model
from settings import NLU_MODEL_PATH, NLU_API_ENDPOINT

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Intent():
    name: str
    confidence: float


@dataclasses.dataclass
class Entity():
    entity: str
    value: str
    start: int
    confidence: float = 1


@dataclasses.dataclass
class ParsedMessage():
    original_message: str
    intent: Intent
    entities: list[Entity]


def test_connection():
    res = requests.get(urllib.parse.urljoin(NLU_API_ENDPOINT, '/status'))
    if res.status_code != 200:
        raise RuntimeError(
            f"Model is unreachable! Status request responded {res.status_code}")


def load_model():
    test_connection()


def parse(message: str) -> ParsedMessage:
    """
    Gives result in the form:
    {
        'intent': {'name': 'find_teacher_by_word', 'confidence': 0.9642855525016785},
        'entities': [
            {'value': 'Nicola', 'entity': 'word'}
        ]
        'original_message': 'find the teacher Nicola'
    }
    :param message: the message to be converted
    :return: the dictionary representing the interpretation
    """

    logger.info('Message to parse: "{}"'.format(message))

    if message.startswith('/'):
        message = message[1:]
        split_message = message.split('{', 1)
        intent_name = split_message[0]
        # added for autocomplete buttons
        if intent_name == 'find_el_by_attr':
            for el in split_message:
                splitted_el = el.split(':', 1)
                if len(splitted_el) > 1:
                    return (parse(
                        splitted_el[1].replace('"', "").replace('}', "")))
        entities = []
        if len(split_message) > 1:  # if there are entities
            entity_list = split_message[1].split(';')
            for i, e in enumerate(entity_list):
                matches = re.findall(
                    r'.*(?:\"|\')(.+?)(?:\"|\'):.*(?:\"|\')(.+?)(?:\"|\').*',
                    e)
                entities.append(Entity(entity=matches[0][0],
                                       value=matches[0][1],
                                       start=i + 1))

        return ParsedMessage(original_message='/' + message,
                             intent=Intent(name=intent_name,
                                           confidence=1),
                             entities=entities)
    else:
        message = message.lower()
        res = requests.post(
            urllib.parse.urljoin(NLU_API_ENDPOINT, '/model/parse'),
            json={'text': message.lower()})
        parsed_message = res.json()

        # parsed_message = inter.parse(message)
        for intent in parsed_message['intent_ranking']:
            if intent['confidence'] > 0.3:
                logger.debug("Message: '%s', Intent: %s, Confidence: %f",
                             message, intent['name'], intent['confidence'])
        for e in parsed_message.get('entities'):
            # del e['start']
            e.pop('end', None)
            e.pop('confidence', None)
            e.pop('extractor', None)
            e.pop('processors', None)
            e['confidence'] = e.pop('confidence_entity', 1)

        logger.info('Parsed message: {}'.format(parsed_message))
        return ParsedMessage(original_message=message,
                             intent=Intent(**parsed_message['intent']),
                             entities=[Entity(**e) for e in
                                       parsed_message.get("entities", [])])
