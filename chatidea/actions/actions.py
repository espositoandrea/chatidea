import copy
import datetime
import logging
import pathlib
import random
import re
from typing import Optional, Any

import matplotlib.pyplot as plt
from pydantic import parse_obj_as

from chatidea import commons, extractor
from chatidea import nltrasnslator, autocompleter
from chatidea.actions import meta
from chatidea.actions.common import action, ActionReturn
from chatidea.config.concept import Attribute
from chatidea.database import resolver
from chatidea.extractor import Entity
from chatidea.patterns import btn, msg, nlu
from chatidea.settings import ELEMENT_VISU_LIMIT, CONTEXT_VISU_LIMIT, \
    ELEMENT_SIMILARITY_DISTANCE_THRESHOLD

logger = logging.getLogger(__name__)


# ENTITIES EXTRACTORS

def extract_entities(entities: list[extractor.Entity], entity_name: str) -> list[extractor.Entity]:
    return [e for e in entities if e.entity.startswith(entity_name)]


def extract_single_entity_value(entities: list[extractor.Entity], entity_name: str) -> Optional[str]:
    found = extract_entities(entities, entity_name)
    return found[0].value if found else None


# takes entities
# for every words gives back a list composed by the word and the attribute that is related to it
def compute_ordered_entity_list(entities: list[extractor.Entity]):
    ordered_entities = []
    index_previous_attribute = None
    index_previous_entity_number_op = None
    for index, e in enumerate(entities):
        ty = None
        op = '='  # the control of the presence of the OP is made here!
        match = re.match("(\w+)_\d+_(\d+)|el_(columns)", e.entity)
        if re.match("attr_\d+_\d+", entities[index - 1].entity):
            index_previous_attribute = entities[index - 1]
        elif entities[index - 1].entity.startswith('op_num'):
            index_previous_entity_number_op = entities[index - 1]
        if match:
            what = match.group(1)
            if what is None:
                what = match.group(3)
            if what == nlu.ENTITY_WORD:
                ty = 'word'
                maybe_op = next((a.value for a in entities if
                                 a.entity.startswith('op_word')), None)
                if maybe_op and maybe_op.endswith('ne'):
                    op = '<>'
                else:
                    op = 'LIKE'  # here forcing the attribute of type "word" to be LIKE and NOT equal
            elif what == nlu.ENTITY_NUMBER:
                ty = 'num'
                if index_previous_entity_number_op:
                    maybe_op = index_previous_entity_number_op.value
                else:
                    maybe_op = None
                maybe_op = commons.extract_similar_value(maybe_op,
                                                         ['less than',
                                                          'more than'], 6)
                if maybe_op:
                    if maybe_op == 'less than':
                        op = '<'
                    elif maybe_op == 'more than':
                        op = '>'
                else:
                    op = '='
            elif what == nlu.ENTITY_COLUMNS:
                ty = 'columns'
                op = 'ORDER BY'
        if ty:
            oe = {'type': ty, 'operator': op, 'value': e.value}
            for index2, e2 in enumerate(entities):
                if index2 == index + 1:
                    if e2.entity == 'or':
                        oe['and_or'] = 'or'
                    elif re.match('attr_\d+_\d+',
                                  e2.entity) or e2.entity == 'and':
                        oe['and_or'] = 'and'
            if ty == 'columns':
                attr = next((a.value for a in entities if
                             re.match("order_by", a.entity)), None)
            else:
                if index_previous_attribute:
                    attr = index_previous_attribute.value
                else:
                    attr = None
            if attr:
                oe['attribute'] = attr
            ordered_entities.append(oe)
            # entities = entities[entities.index(e)+1:]

    return ordered_entities


# ATTRIBUTES HANDLERS
# this is used to map ordered entities to  right columns (this takes care of the join part in case it's needed)
def get_attributes_from_ordered_entities(element_name, ordered_entities) -> list[tuple[Any, str, Attribute]]:
    attributes = []

    for oe in ordered_entities:

        # if the entity has an attribute, i.e. if it not implied
        if oe.get('attribute'):
            order_by_alias = ['order by', 'ordered by', 'sort by', 'sorted by']
            keyword_list = [a.keyword for a in
                            resolver.extract_attributes_with_keyword(
                                element_name)]
            for alias in order_by_alias:
                keyword_list.append(alias)
            attribute_name = commons.extract_similar_value(oe['attribute'],
                                                           keyword_list,
                                                           ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)

            if attribute_name:
                new_attr = resolver.get_attribute_by_name(element_name,
                                                          attribute_name).dict()
                if new_attr:
                    attr = new_attr.copy()
                else:
                    attr = None
                if attr is None and attribute_name in order_by_alias:
                    columns = oe['value']
                    columns_element = handle_columns_name_similarity(
                        element_name, columns)
                    if columns_element:
                        oe['value'] = columns_element
                        attr = {'columns': [columns_element],
                                'keyword': 'order by', 'operator': 'ORDER BY',
                                'type': 'columns', 'value': columns_element}
                    else:
                        raise KeyError(f"Sorry, there is no attribute {columns} for {element_name}")
                if attr.get('type') == oe.get('type'):
                    attr['value'] = oe.get('value')
                    if 'and_or' in oe:
                        attr['and_or'] = oe.get('and_or')
                    attr['operator'] = oe.get('operator',
                                              '=')  # should not happen
                    attributes.append(attr)

            else:  # if it has an attribute but is not recognized
                return []  # something unwanted just happened -> attribute extracted but not matched

        # if the entity does not have an attribute
        else:
            new_attr = resolver.get_attribute_without_keyword_by_type(
                element_name, oe.get('type')).dict()
            if new_attr:
                attr = new_attr.copy()
                attr['value'] = oe.get('value')
                if 'and_or' in oe:
                    attr['and_or'] = oe.get('and_or')
                attr['operator'] = oe.get('operator', '=')
                attributes.append(attr)

    return [(a.pop('value'), a.pop('operator'), parse_obj_as(Attribute, a)) for a in attributes]


def get_attributes_string(attributes: list[tuple[Any, str, Attribute]]):
    return ', '.join(
        ('{} '.format(a.keyword) if a.keyword else '')
        + ('{} '.format(o) if a.type == 'num' else '')
        + str(v) for v, o, a in attributes)


# SIMILARITY HANDLERS

def handle_element_name_similarity(element_name_received: str):
    all_elements_names = resolver.get_all_primary_element_names_and_aliases()
    similar = commons.extract_similar_value(element_name_received,
                                            all_elements_names,
                                            ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return resolver.get_element_name_from_possible_alias(similar)
    return None


def handle_element_relations_similarity(element_name, relation_name_received):
    relations = resolver.extract_relations(element_name)
    all_relations_names = [r['keyword'] for r in relations]
    return commons.extract_similar_value(relation_name_received,
                                         all_relations_names,
                                         ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)


def handle_columns_name_similarity(element_name_alias, columns_name_received):
    displayable_attributes = resolver.simulate_view(element_name_alias)
    attribute_names = [i['attribute'] for i in displayable_attributes if
                       'attribute' in i]
    displayed_names = [i['display'] for i in displayable_attributes if
                       'display' in i]
    similar = commons.extract_similar_value(columns_name_received,
                                            attribute_names,
                                            ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return similar
    else:
        similar = commons.extract_similar_value(columns_name_received,
                                                displayed_names,
                                                ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
        if similar:
            for i in displayable_attributes:
                if i['display'] is similar:
                    return i['attribute']
        else:
            return None

    """element_name = resolver.extract_element(element_name_alias)
    table_name = element_name.get('table_name')
    table_schema = broker.get_table_schema_from_name(table_name)
    all_columns_name = table_schema.get('column_list')
    all_columns_name_alias = table_schema.get('column_alias_list')
    similar = commons.extract_similar_value(columns_name_received, all_columns_name, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
    if similar:
        return similar
    else:
        if all_columns_name_alias:
            all_columns_name_alias_inv = {v: k for k, v in all_columns_name_alias.items()}
            similar = commons.extract_similar_value(columns_name_received, all_columns_name_alias_inv, ELEMENT_SIMILARITY_DISTANCE_THRESHOLD)
            if similar:
                value = all_columns_name_alias_inv.get(similar)
                return value
            else:
                return None
        else:
            return None"""


# RESPONSE HANDLERS

def handle_response_for_quantity_found_element(element) -> ActionReturn:
    if element['real_value_length'] == 1:
        return [msg.ONE_RESULT_FOUND], []
    m = msg.N_RESULTS_FOUND_PATTERN.format(element['real_value_length'])
    if element.get('action_type') == 'filter' or element.get(
            'element_name') not in resolver.get_all_primary_element_names():
        return [m], []
    return [m, msg.REMEMBER_FILTER], [
        btn.get_button_filter_hints(),
        btn.get_button_history()
    ]


# SELECTION HANDLERS

def is_selection_valid(element, position):
    return 0 < position <= len(
        element['value'])  # element['real_value_length']:


def add_selected_element_to_context(element, position, context):
    # copying the dictionary
    selected_element = dict(element)

    # I must save it as a list
    selected_element['value'] = [element['value'][position - 1]]
    selected_element['query'] = None
    selected_element['real_value_length'] = 1
    selected_element['action_name'] = '...selected from:'
    selected_element['action_type'] = 'select'

    context.append_element(selected_element)


def is_value_in_selection_valid(element, position, title):
    # copying the dictionary
    selected_element = dict(element)
    # I must save it as a list
    selected_element['value'] = [element['value'][position - 1]]
    match = resolver.get_element_show_string(selected_element['element_name'],
                                             selected_element['value'][0])
    match = clean_title_for_selection(match)
    if match[:29] == title:  # 29 chars is max title payload
        return True
    else:
        return False


def clean_title_for_selection(title):
    title = msg.cleanhtml(title)
    clean = re.compile('"|;')
    title = re.sub(clean, '', title)
    clean = re.compile("'")
    title = re.sub(clean, '', title)
    title = title.rstrip()
    return title


# ACTIONS

@action
def action_more_info_find(entities, context, add=True) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)

    name = extract_single_entity_value(entities, nlu.ENTITY_ELEMENT)
    element_name = handle_element_name_similarity(name) if name else None

    if not element_name:
        return ['I am sorry, I understood that you want more info, but not on what...'], base_buttons

    logger.info("Recognized element: %s", element_name)
    if add:
        element = {'value': 0, 'element_name': 'more_info_find',
                   'element_value': element_name,
                   'action_name': 'more info find',
                   'action_type': 'more_info_find', 'entities': entities,
                   'query': None, 'real_value_length': 1}
        context.append_element(element)

    base_buttons = [btn.get_button_show_more_examples(element_name)] + base_buttons
    category = resolver.extract_categories(element_name)
    if category:
        base_buttons = btn.get_button_show_table_categories(element_name) + base_buttons

    return [msg.find_element_examples(element_name)], base_buttons


@action
def action_more_info_filter(entities, context) -> ActionReturn:
    base_buttons = [
        btn.get_button_help_on_elements(),
        btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
        btn.get_button_history()
    ]
    name = extract_single_entity_value(entities, nlu.ENTITY_ELEMENT)
    element_name = handle_element_name_similarity(name) if name else None
    if element_name:
        return [msg.filter_element_examples(element_name)], base_buttons
    element = context.get_last_element()
    if element and element['real_value_length'] > 1:
        return [msg.filter_element_examples(element['element_name'])], base_buttons
    else:
        return ["I am sorry, but there is nothing to filter... You'd better tell on which element.\n"
                f'Try, for instance, with "how to filter {resolver.get_all_primary_element_names()[0]}"'], base_buttons


def find_word_el_number(entities: list[Entity]):
    for i in range(0, len(entities)):
        match = re.match(r"(\w+)_(\d+)_(\d+)", entities[i].entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                return match.group(2)


def find_el_number(entities: list[Entity]):
    for i in range(0, len(entities)):
        match = re.match(r"(\w+)_(\d+)", entities[i].entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                return int(match.group(2))
    return 0


def find_word_numbers(entities: list[Entity]):
    for i in range(0, len(entities)):
        match = re.match(r"(\w+)_(\d+)_(\d+)", entities[i].entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                return str(match.group(2) + "_" + match.group(3))
    return 0


def replace_el_name(entities: list[Entity], name):
    for i in range(0, len(entities)):
        match = re.match("(\w+)_(\d+)", entities[i].entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                entities[i].value = name


def replace_word_numbers(entities: list[Entity], numbers):
    for i in range(0, len(entities)):
        match = re.match("(\w+)_(\d+)_(\d+)", entities[i].entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_WORD:
                entities[i].entity = "word_" + numbers


def remove_el(entities: list[extractor.Entity]):
    for i in entities:
        match = re.match("(\w+)_(\d+)", i.entity)
        if match:
            what = match.group(1)
            if what == nlu.ENTITY_ELEMENT:
                entities.remove(i)


@action
def action_ambiguity_solver(entities: list[extractor.Entity], context) -> ActionReturn:
    name = extract_single_entity_value(entities, nlu.ENTITY_ELEMENT)
    element_name = handle_element_name_similarity(name) if name else None
    replace_el_name(entities, element_name)

    if not contain(entities, nlu.ENTITY_WORD) and not contain(entities, nlu.ENTITY_NUMBER):
        return action_find_element_by_attribute(entities, context).get_components()

    el_number = int(find_el_number(entities))
    word_el_number = int(find_word_el_number(entities))

    if contain(entities, nlu.ENTITY_ELEMENT) and el_number == word_el_number:
        new_entities = entities.copy()
        autocompleter.autocomplete_from_word(new_entities)

    else:
        for e in entities:
            e.entity = e.entity.replace("num", "word")

        all_similar_words = resolver.extract_similar_values(find_word_numbers(entities))
        remove_el(entities)
        for word in all_similar_words:
            new_entities = entities.copy()
            replace_word_numbers(new_entities, word)
            autocompleter.autocomplete_from_word(new_entities)

    return nltrasnslator.build_response(context)


def contain(entities: list[extractor.Entity], word):
    if word == nlu.ENTITY_ELEMENT:
        for i in entities:
            match = re.match("(\w+)_(\d+)", i.entity)
            if match:
                what = match.group(1)
                if what == nlu.ENTITY_ELEMENT:
                    return True
    else:
        for e in entities:
            match = re.match("(\w+)_(\d+)_(\d+)",
                             e.entity)  # for word e attr
            if match and match.group(1) == word:
                return True
    return False


@action
def action_find_element_by_attribute(entities: list[extractor.Entity], context) -> ActionReturn:
    name = extract_single_entity_value(entities, nlu.ENTITY_ELEMENT)
    element_name = handle_element_name_similarity(name) if name else None
    ordered_entities = compute_ordered_entity_list(entities)

    if not element_name:
        return [
            'I guess you want to find something, but I did not understand what!\n',
            msg.element_names_examples()
        ], [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history(),
        ]

    try:
        attributes = get_attributes_from_ordered_entities(element_name, ordered_entities) if ordered_entities else []
    except KeyError as e:
        return [str(e)], [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]
    if not attributes:
        return [(
            f'Ok so you want to find some concepts of type {element_name}, but you should '
            'tell me something more, otherwise I can\'t help you explore!'),
            msg.find_element_examples(element_name)
        ], [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]
    element = resolver.query_find(element_name, attributes)
    if not element['value']:
        return [msg.NOTHING_FOUND], [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]
    element['action_name'] = f'...found with attribute(s) "{get_attributes_string(attributes)}"'
    element['action_type'] = 'find'
    context.append_element(element)
    # handle_response_for_quantity_found_element(response, element, context)
    return action_view_context_element(entities, context).get_components()


@action
def action_filter_element_by_attribute(entities, context) -> ActionReturn:
    element = context.get_last_element()
    if not element:
        return [msg.EMPTY_CONTEXT_LIST], []

    if element['real_value_length'] <= 1:
        return ['Filtering is not possible now, there is only one element under to view!'], [
            btn.get_button_help_on_elements(),
            # response.add_message('Remember that you can always go back, just click the button')
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]

    ordered_entities = compute_ordered_entity_list(entities)
    attributes = get_attributes_from_ordered_entities(
        element['element_name'], ordered_entities)

    if not attributes:
        msg, btns = action_more_info_filter(entities, context).get_components()
        return ["I didn't understand for what do you want to filter by\n", msg], btns

    # here down union of attributes
    all_attributes = copy.deepcopy(element['attributes']) if element.get('attributes') else []
    if all_attributes[-1]['keyword'] == 'order by':  # 'and' the last where in the context with the first of the filter
        all_attributes[-1]['and_or'] = 'and'
    else:
        all_attributes[-1]['and_or'] = 'and'
    all_attributes += copy.deepcopy(attributes)
    result_element = resolver.query_find(element['element_name'], all_attributes)
    if not result_element['value']:
        error_message = f"Nothing as been found for {element['element_name']} "
        error_message += ", ".join([f"{e['attribute']} {e['value']}" for e in ordered_entities])
        return [error_message], [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]

    result_element['action_name'] = f'...by filtering with property(s) "{get_attributes_string(attributes)}":'
    result_element['action_type'] = 'filter'
    context.append_element(result_element)
    m1, b1 = handle_response_for_quantity_found_element(result_element)
    m2, b2 = action_view_context_element(entities, context).get_components()
    return m1 + m2, b1 + b2


@action
def action_cross_relation(entities, context) -> ActionReturn:
    element = context.get_last_element()

    if not element:
        return [msg.ERROR], [btn.get_button_help_on_elements()]

    extracted_relation_name = extract_single_entity_value(entities, nlu.ENTITY_RELATION)
    relation_name = handle_element_relations_similarity(element['element_name'], extracted_relation_name)

    # control if there is ONLY an element in context_list
    if not relation_name or element['real_value_length'] != 1:
        return [msg.ERROR], [btn.get_button_help_on_elements()]

    result_element = resolver.query_join(element, relation_name)
    if not result_element['value']:
        return [msg.NOTHING_FOUND], [
            btn.get_button_help_on_elements(),
            btn.get_button_view_context_element('- GO BACK TO THE CONCEPT! -'),
            btn.get_button_history()
        ]

    result_element['action_name'] = f'...reached with the relation "{relation_name}", from {element["element_name"]}:'
    result_element['action_type'] = 'cross'
    context.append_element(result_element)
    return action_view_context_element(entities, context).get_components()


@action
def action_show_relations(entities, context) -> ActionReturn:
    element = context.get_last_element()
    if not element:
        return [msg.EMPTY_CONTEXT_LIST], []
    buttons = btn.get_buttons_element_relations(element['element_name'])
    if not buttons:
        return [], []
    return ['If you want more information, I can tell you:'], buttons


@action
def action_select_element_by_position(entities: list[extractor.Entity], context) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)
    pos = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    title = extract_single_entity_value(entities, 'title')

    if not pos:
        return [msg.ERROR], base_buttons
    # attention, I suppose "position" is in the form "1st", "2nd", ...
    position = int(pos)

    element = context.get_last_element()

    if not element:
        return [msg.EMPTY_CONTEXT_LIST], base_buttons
    if element['real_value_length'] == 1:
        m, b = action_view_context_element(entities, context)
        return ['There is only one element!\n'] + m, b
    if not is_selection_valid(element, position):
        return ['Error! Out of range selection!'], base_buttons
    if not is_value_in_selection_valid(element, position, title):
        return ['Error! The selected element not belonging to the context!'], base_buttons
    add_selected_element_to_context(element, position, context)
    return action_view_context_element(entities, context).get_components()


@action
def action_view_context_element(entities, context, show_less=False) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)
    element = context.view_last_element()
    previous_element = context.view_second_to_last_element()
    if not element:
        return [msg.EMPTY_CONTEXT_LIST], base_buttons
    if element['element_name'] == "more_info_find":
        return action_more_info_find(element['entities'], context, False).get_components()

    if element['element_name'] == "start":
        return meta.start(element['entities'], context, False).get_components()

    if element['element_name'] == "show_table_categories":
        return action_show_table_categories(element['entities'], context, False).get_components()

    messages = []
    buttons = []
    if element['real_value_length'] == 1:
        messages.append(msg.element_attributes(element))
        if element.get('element_name') in resolver.get_all_primary_element_names():
            m, b = action_show_relations(entities, context).get_components()
            messages += m
            buttons += b
    else:
        if element['show']['from'] == 0 and not show_less:
            messages.append(msg.SELECT_FOR_INFO_PATTERN.format(element.get('element_name')))
        messages.append(
            f'Shown results from {element["show"]["from"] + 1} to {element["show"]["to"]} of {element["real_value_length"]}')

        buttons += btn.get_buttons_select_element(element)
        if element['show']['to'] < element['real_value_length']:
            buttons.append(btn.get_button_show_more_element())
        if element['show']['from'] >= 1:
            buttons.append(btn.get_button_show_less_element())
        buttons.append(btn.get_button_order_by())
        buttons.append(btn.get_button_filter_hints())
    return messages, buttons + base_buttons


@action
def action_show_more_elements(entities, context) -> ActionReturn:
    element = context.get_last_element()
    if not element or element['real_value_length'] <= 1:
        return ['I am sorry, but there is nothing to show more...'], []
    if element['show']['to'] >= element['real_value_length']:
        return ['I am sorry, but there is nothing to show more...'], []
    element['show']['from'] = element['show']['from'] + ELEMENT_VISU_LIMIT
    element['show']['to'] = min(element['real_value_length'],
                                element['show']['to'] + ELEMENT_VISU_LIMIT)
    context.reset_show_last_element = False
    return action_view_context_element(entities, context).get_components()


@action
def action_show_less_elements(entities, context) -> ActionReturn:
    element = context.get_last_element()
    if not element or element['real_value_length'] <= 1 or element['show']['to'] <= ELEMENT_VISU_LIMIT:
        return ['I am sorry, but there is nothing to show less...'], []

    diff = 0
    if element['show']['to'] == element['real_value_length']:
        diff = element['show']['to'] - (element['show']['from'] + 1)
    element['show']['to'] = element['show']['to'] - ELEMENT_VISU_LIMIT
    element['show']['to'] += diff
    element['show']['from'] = max(0, element['show']['from'] - ELEMENT_VISU_LIMIT)
    context.reset_show_last_element = False
    return action_view_context_element(entities, context, show_less=True).get_components()


@action
def action_order_by(entities, context) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)
    element = context.get_last_element()
    if not element:
        return ['I am sorry, but there is nothing to order...'], base_buttons
    else:
        value = element['value']
        element_name = element['element_name']
        value_attributes = value[0]  # take first element
        return ['Choose the property you want to order'], btn.get_buttons_order_by_attribute(value_attributes,
                                                                                             element_name) + base_buttons


@action
def action_order_by_attribute(entities, context) -> ActionReturn:
    attribute_to_order_by = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    element = context.get_last_element()
    value = element['value']
    # All None element are put in the end
    value = sorted(value, key=lambda k: (k[attribute_to_order_by] is None, k[attribute_to_order_by]))
    element['value'] = value
    context.reset_show_last_element = False
    return action_view_context_element(entities, context).get_components()


@action
def action_show_more_examples(entities: list[Entity], context) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)
    element_name = entities[0].value
    attributes = resolver.extract_all_attributes(element_name)
    return [f'Select the property of "{element_name}" you want to see examples of'], \
        btn.get_buttons_show_more_ex_attr(element_name, attributes) + base_buttons


@action
def action_show_more_examples_attribute(entities: list[extractor.Entity],
                                        context) -> ActionReturn:
    for e in entities:
        if e.entity == 'e':
            element_name = e.value
        elif e.entity == 'k':
            key = '' if e.value == ' ' else e.value
    attribute = resolver.get_attribute_by_name(element_name, key)
    if not attribute:
        attribute = resolver.get_attribute_without_keyword(element_name)
    if 'by' in attribute:
        new_table_name = attribute.by[-1].to_table
        new_element_name = resolver.get_element_name_from_table_name(
            new_table_name)
        examples = resolver.query_show_attributes_examples(new_element_name,
                                                           attribute.columns)
        attribute_alias = resolver.extract_attributes_alias(new_element_name)
    else:
        examples = resolver.query_show_attributes_examples(element_name,
                                                           attribute.columns)
        attribute_alias = resolver.extract_attributes_alias(element_name)
    columns = []
    for c in attribute.columns:
        if attribute_alias and c in attribute_alias:
            columns.append(attribute_alias[c])
        else:
            columns.append(c)
    attribute_message = ""
    loop = True
    i = 0
    # for _ in range(10):
    while loop:
        # attribute_message += "{}, ".format(random.choice(examples))
        attribute_message += f"- Find {element_name} "
        if attribute['keyword']:
            attribute_message += f"{attribute['keyword']} "
        example = random.choice(examples)
        examples.remove(example)
        attribute_message += "{}\n".format(example)
        i += 1
        if i == 9 or not examples:
            loop = False
    return [attribute_message], btn.get_base_buttons(context)


@action
def action_show_context(entities, context) -> ActionReturn:
    context_list = context.view_context_list()  # _to_show()
    if not context_list:
        return [msg.EMPTY_CONTEXT_LIST], btn.get_base_buttons(context)
    up = context.context_list_indices['up']
    down = context.context_list_indices['down']

    messages = []
    buttons = []

    for i, el in enumerate(context_list[down:up][::-1]):
        if el['element_name'] == "more_info_find":
            result = f'Examples of "{el["element_value"]}"'
        elif el['element_name'] == "start":
            result = 'Start'
        elif el['element_name'] == "show_table_categories":
            result = f'Categories of "{el["element_value"]}"'
        elif el['real_value_length'] == 1:
            result = f"{resolver.get_element_show_string(el['element_name'], el['value'][0])}"
        else:
            result = f'A list of type "{el["element_name"]}"'

        if up == len(context_list) and i == 0:
            messages.append("Here is history, click on a button to see the related element")
            buttons.append(btn.get_button_view_context_element(result))
        else:
            buttons.append(btn.get_button_go_back_to_context_position(result, up - i))

    buttons.append(btn.get_button_reset_context())
    if down != 0:
        buttons.append(btn.get_button_show_more_context())

    return messages, buttons + btn.get_base_buttons(context)


@action
def action_show_more_context(entities, context) -> ActionReturn:
    context_list = context.get_context_list()

    if not context_list:
        return ['I am sorry, but there is nothing to show more...'], btn.get_base_buttons(context)
    if context.context_list_indices['down'] == 0:
        return ['I am sorry, but there is nothing to show more...'], btn.get_base_buttons(context)
    context.context_list_indices['down'] = max(context.context_list_indices['down'] - CONTEXT_VISU_LIMIT, 0)
    context.context_list_indices['up'] = context.context_list_indices['up'] - CONTEXT_VISU_LIMIT
    context.reset_show_context_list = False
    return action_show_context(entities, context).get_components()


@action
def action_go_back_to_context_position(entities, context) -> ActionReturn:
    pos = extract_single_entity_value(entities, nlu.ENTITY_POSITION)
    if not context.get_context_list():
        return [msg.EMPTY_CONTEXT_LIST], btn.get_base_buttons(context)
    length = len(context.get_context_list())
    position = int(pos) if pos else (length - 1)
    # if no position is extracted, set the value to go back only once

    if position == nlu.VALUE_POSITION_RESET_CONTEXT or \
            len(context.get_context_list()) == 1 and position == 0:  # if the list is one el long and no entity pos
        context.reset_context_list()
        if position == nlu.VALUE_POSITION_RESET_CONTEXT:
            return [msg.CONTEXT_LIST_RESET], btn.get_base_buttons(context)
        else:
            return [msg.NO_GO_BACK], btn.get_base_buttons(context)
    elif position - 1 < length:
        context.go_back_to_position(position)
        m, b = action_view_context_element(entities, context).get_components()
        return [
                   f'Ok, now resuming your history of {length - position} position{"s" if length - position > 1 else ""}... DONE!'] + m, b

    else:
        # wrong selection
        return action_show_context(entities, context).get_components()


@action
def action_find_element_by_category(entities: list[Entity], context) -> ActionReturn:
    element = context.get_last_element()
    if not element:
        return [], []
    element_name = element['element_value']
    category_name = entities[0].entity
    category_value = entities[0].value
    if not element_name or not category_value:
        return [msg.ERROR], []
    element = resolver.query_category_value(element_name, category_name, category_value)
    if not element['value']:
        return [msg.NOTHING_FOUND], []

    element['action_name'] = f'...found from category {category_value} of table {element_name.upper()}'
    element['action_type'] = 'find'
    context.append_element(element)
    # handle_response_for_quantity_found_element(response, element, context)
    return action_view_context_element(entities, context).get_components()


@action
def action_show_table_categories(entities: list[Entity], context, add=True) -> ActionReturn:
    base_buttons = btn.get_base_buttons(context)
    element_name = entities[0].entity
    category_column = entities[0].value
    category = resolver.extract_category(element_name, category_column)
    if not element_name:
        return [msg.NOTHING_FOUND], base_buttons

    if not category:
        return [f"I cannot find more info about {element_name}s."], base_buttons

    element = resolver.query_category(element_name, category)
    plot_file = create_plot(element, (category.alias or category.column).upper(), session=context.session)

    if add:
        context.append_element({
            'value': 0, 'element_name': 'show_table_categories', 'element_value': element_name,
            'action_name': 'show_table_categories', 'action_type': 'show_table_categories', 'entities': entities,
            'query': None, 'real_value_length': 1
        })

    return [
        f'The concepts of type {element_name} can be categorized based on {category.alias}.',
        f'/pie-chart {plot_file}',
        f'You can select {element_name}s related to a specific category by clicking on the related button.'
    ], btn.get_buttons_select_category(element_name, category.alias, element['value']) + base_buttons


def create_plot(categories, legend_title, session: Optional[str] = None) -> pathlib.Path:
    plt.switch_backend('Agg')

    total = 0
    labels = []
    sizes = []
    perc = []
    items = categories['value']
    displayed_items = 5 if len(items) > 5 else len(items)

    for i in items:
        total += i['count']

    for i in range(displayed_items):
        labels.append(items[i]['category'])
        sizes.append(items[i]['count'])
        perc.append(sizes[i] * 100 / total)

    if displayed_items < len(items):
        other_count = 0
        for i in range(displayed_items, len(items)):
            other_count += items[i]['count']
        labels.append('Other')
        sizes.append(other_count)
        perc.append(sizes[displayed_items] * 100 / total)

    colors = ['tomato', 'mediumseagreen', 'pink', 'darkturquoise', 'gold',
              'dimgrey']
    patches, texts = plt.pie(sizes, colors=colors, autopct=None, startangle=90,
                             labeldistance=None, textprops={'fontsize': 14},
                             wedgeprops={'linewidth': 0.5,
                                         'edgecolor': 'black'})
    plt.legend(patches,
               labels=['%s, %1.1f %%' % (l, p) for l, p in zip(labels, perc)],
               title=legend_title, title_fontsize='large', loc='lower center',
               bbox_to_anchor=(0.5, 1))

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"pie-{timestamp}.png" if not session else f"pie-{session}-{timestamp}.png"
    base = pathlib.Path("static")
    base.mkdir(exist_ok=True, parents=True)
    plt.axis('equal')
    plt.savefig(base / filename, bbox_inches="tight")
    plt.close()
    return base / filename
