import logging

from chatidea.config import DatabaseConcepts
from chatidea.config.concept import Concept
from chatidea.config.view import ColumnView
from chatidea.database import broker
from chatidea.settings import DB_CONCEPT, DB_CONCEPT_S

logger = logging.getLogger(__name__)

db_concept: DatabaseConcepts = []
db_concept_s = []


# Database properties


def load_db_concept():
    global db_concept
    global db_concept_s
    db_concept = DB_CONCEPT
    db_concept_s = DB_CONCEPT_S


def extract_similar_values(word):
    all_words = []
    for e in db_concept_s:
        for s in e.get('similars'):
            if word in s:
                all_words = s
    if len(all_words) == 0:
        all_words = [word]
    return all_words


def get_all_primary_element_names():
    res = []
    for e in db_concept:
        if e.type == 'primary':
            res.append(e.element_name)
    return res


def get_all_primary_elements() -> list[Concept]:
    return [e for e in db_concept if e.type == "primary"]


def get_all_primary_element_names_and_aliases() -> list[set[str]]:
    return [{e.get_element_name(False), e.get_element_name(True), *e.aliases} for e in get_all_primary_elements()]


def get_element_aliases(element_name: str):
    element = extract_element(element_name)
    return element.aliases or []


def get_element_from_possible_alias(element_or_alias_name: str):
    for e in db_concept:
        if e.get_element_name(False) == element_or_alias_name or e.get_element_name(
                True) == element_or_alias_name or element_or_alias_name in e.aliases:
            return e
    return None


def get_element_name_from_possible_alias(element_or_alias_name: str):
    e = get_element_from_possible_alias(element_or_alias_name)
    return e.element_name if e else None


def get_element_name_from_table_name(table_name: str):
    for e in db_concept:
        if e.table_name == table_name:
            return e.element_name
    return None


def extract_element(element_name: str):
    for e in db_concept:
        if e.element_name == element_name:
            return e
    return None


def extract_show_columns(element_name: str):
    e = extract_element(element_name)
    return e.show_columns if e else None


def extract_relations(element_name: str):
    e = extract_element(element_name)
    return e.relations if e else None


def extract_all_attributes(element_name: str):
    e = extract_element(element_name)
    return e.attributes if e else None


def extract_categories(element_name: str):
    e = extract_element(element_name)
    return e.category if e else None


def extract_category(element_name: str, column_name: str):
    e = extract_element(element_name)
    for c in e.category:
        if c.column == column_name or c.alias == column_name:
            return c
    return None


def extract_attributes_with_keyword(element_name: str):
    attributes = extract_all_attributes(element_name)
    if attributes:
        return [a for a in attributes if a.keyword]
    return None


def extract_attributes_alias(element_name: str):
    e = extract_element(element_name)
    table_name = e.table_name
    table_schema = broker.get_table_schema_from_name(table_name)
    return table_schema.column_alias_list


def get_attribute_by_name(element_name: str, attribute_name: str):
    attributes = extract_attributes_with_keyword(element_name)
    for a in attributes:
        if a.keyword == attribute_name:
            return a
    return None


def get_attribute_without_keyword_by_type(element_name: str,
                                          attribute_type: str):
    attributes = [a for a in extract_all_attributes(element_name)
                  if a not in extract_attributes_with_keyword(element_name)]
    for a in attributes:
        if a.type == attribute_type:
            return a
    return None


def get_attribute_without_keyword(element_name):
    attributes = [a for a in extract_all_attributes(element_name) if
                  a not in extract_attributes_with_keyword(element_name)]
    for a in attributes:
        return a
    return None


def get_element_show_string(element_name, element_value):
    show_columns = extract_show_columns(element_name)
    return ', '.join((sh.keyword + ': ' if sh.keyword else '')
                     + ' '.join(str(element_value[x]) for x in sh.columns)
                     for sh in show_columns)


def query_find(element_name, attributes):
    e = extract_element(element_name)
    table_name = e.table_name
    result_element = broker.query_find(table_name, attributes)
    result_element['element_name'] = element_name
    return result_element


def query_show_attributes_examples(element_name, attributes):
    e = extract_element(element_name)
    table_name = e.table_name
    result_element = broker.query_show_attributes_examples(table_name,
                                                           attributes)
    result_element = list(filter(None, result_element))
    return result_element


def query_join(element, relation_name):
    all_relations = extract_relations(element['element_name'])

    # there should always be the relation we want, the control is made in the executor
    relation = \
        [rel for rel in all_relations if rel['keyword'] == relation_name][0]

    result_element = broker.query_join(element, relation)
    result_element['element_name'] = relation['element_name']
    return result_element


def query_category(element_name, category):
    e = extract_element(element_name)
    table_name = e.table_name
    result_element = broker.query_category(table_name, category)
    result_element['element_name'] = element_name
    return result_element


def query_category_value(element_name, category_column, category_value):
    e = extract_element(element_name)
    table_name = e.table_name
    category = extract_category(element_name, category_column)
    result_element = broker.query_category_value(e.element_name,
                                                 table_name, category,
                                                 category_value)
    result_element['element_name'] = element_name
    return result_element


def simulate_view(element_name) -> list[ColumnView]:
    e = extract_element(element_name)
    table_name = e.table_name
    result_element = broker.simulate_view(table_name)
    return result_element
