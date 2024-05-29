import copy
import random
import re

from chatidea.config.concept import Attribute
from chatidea.database import resolver
from chatidea.settings import EXTRA_CONFIG

HI_THERE = EXTRA_CONFIG.greeting

REMEMBER_HISTORY = EXTRA_CONFIG.help_history
REMEMBER_GO_BACK = EXTRA_CONFIG.help_go_back
ERROR = EXTRA_CONFIG.error
FINDING_ELEMENT = EXTRA_CONFIG.finding_element
NOTHING_FOUND = EXTRA_CONFIG.nothing_found
ONE_RESULT_FOUND = EXTRA_CONFIG.one_result_found
N_RESULTS_FOUND_PATTERN = EXTRA_CONFIG.n_results_found_pattern
REMEMBER_FILTER = EXTRA_CONFIG.help_filter
SELECT_FOR_INFO_PATTERN = EXTRA_CONFIG.select_for_info_pattern
INTRODUCE_ELEMENT_TO_SHOW_PATTERN = EXTRA_CONFIG.introduce_element_to_show_pattern
AMBIGUITY_FOUND = EXTRA_CONFIG.ambiguity_found
EMPTY_CONTEXT_LIST = EXTRA_CONFIG.empty_context_list
CONTEXT_LIST_RESET = EXTRA_CONFIG.context_list_reset
NO_GO_BACK = EXTRA_CONFIG.no_go_back
REMEMBER_RESET_HISTORY = EXTRA_CONFIG.remember_reset_history


def element_attributes(element):
    # value = copy.deepcopy(element['value'][0])
    # value_with_alias = {}
    # attributes_alias = resolver.extract_attributes_alias(element['element_name'])
    # if attributes_alias:
    #    for k,v in value.items():
    #        if k in attributes_alias:
    #            value_with_alias[attributes_alias[k]] = v
    #        else:
    #            value_with_alias[k] = v
    #    value = copy.deepcopy(value_with_alias)
    msg = '{}\n'.format(element['element_name'].upper())
    displayable_attributes = resolver.simulate_view(element['element_name'])
    attribute_names = [i.attribute for i in displayable_attributes]
    displayed_names = [i.display for i in displayable_attributes]
    for k, v in element['value'][0].items():
        if k in attribute_names:
            i = attribute_names.index(k)
            msg += '\n\n- {0}: {1}'.format(displayed_names[i],
                                           cleanhtml(str(v)))
    # taking only first value
    # msg += '\n'.join(['- {0}: {1}'.format(k, v) for k, v in value.items()])
    return msg


def element_list(element):
    msg = ''
    for i in range(element['show']['from'], element['show']['to']):
        msg += '{}. {}\n'.format(i + 1, resolver.get_element_show_string(
            element['element_name'], element['value'][i]))
    return msg


def find_element_action_name(element_name, ordered_entities):
    stringified_entities = []
    for oe in ordered_entities:
        se = '"'
        if oe.get('attribute'):
            se += oe['attribute'] + ' '
        se += str(oe['value']) + '"'
        stringified_entities.append(se)
    return '[Finding by attributes] {}'.format(element_name,
                                               ' ,'.join(stringified_entities))


def element_names_examples():
    elements = resolver.get_all_primary_element_names()
    message = 'I understand phrases related to '
    message += ', '.join(elements) + '.'
    message += '\nAsk me more information about such concepts.'
    return message


def get_message_example(element_name, a:Attribute, keyword_list):
    message = "- Find {} ".format(element_name)
    if a.keyword:
        keyword_list.append(a.keyword)
        #  keyword_list_with_col[a.get('keyword')] = a.get('columns')
        message += "{} ".format(a.keyword)
    if a.type == 'num':
        message += "more than / less than "
    if a.by:
        new_table_name = a.by[-1].to_table_name
        new_element_name = resolver.get_element_name_from_table_name(
            new_table_name)

        examples = resolver.query_show_attributes_examples(new_element_name,
                                                           a.columns)
        # attributes_alias = resolver.extract_attributes_alias(new_element_name)
    else:
        # attributes_alias = resolver.extract_attributes_alias(element_name)
        examples = resolver.query_show_attributes_examples(element_name,
                                                           a.columns)
    """if attributes_alias:
        for c in a['columns']:
            if c in attributes_alias:
                columns.append(attributes_alias[c])
                if a.get('keyword'):
                    if a.get('keyword') in keyword_list_with_col:
                        keyword_list_with_col[a.get('keyword')].append(attributes_alias[c])
                    else:
                        keyword_list_with_col[a.get('keyword')] = [attributes_alias[c]]
            else:
                columns.append(c)
                if a.get('keyword'):
                    if a.get('keyword') in keyword_list_with_col:
                        keyword_list_with_col[a.get('keyword')].append(c)
                    else:
                        keyword_list_with_col[a.get('keyword')] = [c]
    else:
        if a.get('keyword'):
            keyword_list_with_col[a.get('keyword')] = a.get('columns')
        columns = a.get('columns')"""

    # message += "{} (e.g. {},{},{})\n" .format(columns,random.choice(examples),random.choice(examples),random.choice(examples))
    message += "{} \n".format(random.choice(examples))
    return message


def find_element_examples(element_name):
    # message = 'I am able to find elements of type {} in many different ways. ' \
    # 'Here some options, I hope they can fit your purposes!\n Inside the bracket [ ]   you will find the names of the attributes accepted and in the [e.g] you can find some examples of that attributes that you can use \n\n'.format(element_name)
    message = "I am able to find {}'s properties in many different ways. \nHere some examples, I hope they can fit your purposes!\n".format(
        element_name)

    keyword_list = []
    attributes = resolver.extract_all_attributes(element_name)
    # all_el_names = [element_name] + resolver.get_element_aliases(element_name)
    if attributes:  # will be deleted when all elements will have at least 1 attribute
        for a in attributes:
            message += get_message_example(element_name, a, keyword_list)
        message += "\nYou can also do properties combinations like:\n"
        if keyword_list:
            attributes_copy = copy.deepcopy(attributes)
            if len(attributes_copy) > 2:
                attributes_copy.pop(0)
                attr = random.choice(attributes_copy)
                attributes_copy.remove(attr)
                attr2 = random.choice(attributes_copy)

                message_to_add = get_and_or_examples(element_name, attr,
                                                     keyword_list)
                message += "- Find {} {} ".format(element_name, message_to_add)
                message_to_add = get_and_or_examples(element_name, attr2,
                                                     keyword_list)
                message += "{}\n".format(message_to_add)
                attributes_copy.append(attr)

                attr = random.choice(attributes_copy)
                attributes_copy.remove(attr)
                attr2 = random.choice(attributes_copy)

                message_to_add = get_and_or_examples(element_name, attr,
                                                     keyword_list)
                message += "- Find {} {} ".format(element_name, message_to_add)
                message_to_add = get_and_or_examples(element_name, attr2,
                                                     keyword_list)
                message += "{} ".format(message_to_add)
                attributes_copy.append(attr)
                attr = random.choice(attributes_copy)
                message_to_add = get_and_or_examples(element_name, attr,
                                                     keyword_list)
                message += "{}\n".format(message_to_add)

                attr = random.choice(attributes_copy)
                attributes_copy.remove(attr)
                attr2 = random.choice(attributes_copy)
                message_to_add = get_and_or_examples(element_name, attr,
                                                     keyword_list)
                message += "- Find {} {} or ".format(element_name,
                                                     message_to_add)
                message_to_add = get_and_or_examples(element_name, attr2,
                                                     keyword_list)
                message += "{}\n".format(message_to_add)
            else:
                or1 = get_and_or_examples(element_name, attributes[0],
                                          keyword_list)
                or2 = get_and_or_examples(element_name, attributes[0],
                                          keyword_list)
                message += "- Find {} {} or {}".format(element_name, or1, or2)
        else:
            or1 = get_and_or_examples(element_name, attributes[0],
                                      keyword_list)
            or2 = get_and_or_examples(element_name, attributes[0],
                                      keyword_list)
            message += "- Find {} {} or {}".format(element_name, or1, or2)
    else:
        message = '- no attribute- Find {}  has been defined for {} yet -'.format(
            element_name, element_name)
    print(message)
    return message.replace("[", "(").replace("]",
                                             ")")  # these 2 replace are just here in case of webchat interface


def get_and_or_examples(element_name, attribute, keyword_list):
    message_to_add = get_message_example(element_name, attribute, keyword_list)
    element_name_number_of_words = len(element_name.split())
    cut_string = element_name_number_of_words + 2
    message_to_add = ' '.join(message_to_add.split()[cut_string:])
    return message_to_add


"""def find_element_combinations(element_name, attribute):
    message = 'I am able to understand combinations like: \n'
    all_el_names = [element_name] + resolver.get_element_aliases(element_name)
    message += "- Find {} ".format(random.choice(all_el_names))
    keyword_list = []
    keyword_list_with_col = {}
    messages_to_add = []
    for a in attribute:
        message_to_add = get_message_example(element_name, a, keyword_list, keyword_list_with_col)
        message_to_add = ' '.join(message_to_add.split()[3:])
        messages_to_add.append(message_to_add)
    messages_to_add.pop(0)
    if messages_to_add:
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice + " "
    if messages_to_add:
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice + '\n'

    if messages_to_add:
        message += "- Find {} ".format(random.choice(all_el_names))
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice + " "
    if messages_to_add:
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice + " "
    if messages_to_add:
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice + '\n'

    if messages_to_add:
        message += "- Find {} ".format(random.choice(all_el_names))
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += random_choice
    if messages_to_add:
        random_choice = random.choice(messages_to_add)
        messages_to_add.remove(random_choice)
        message += " or "+ random_choice + '\n'
    return message"""


def filter_element_examples(element_name):
    message = 'How to filter concepts of type {}? Here some hints:\n'.format(
        element_name)
    attributes = resolver.extract_all_attributes(element_name)
    if attributes:  # will be deleted when all elements will have at least 1 attribute
        for a in attributes:
            message += "- Filter those "
            if a.keyword:
                message += "{} ".format(a.keyword)
            if a.type == 'num':
                message += "more than " if random.randint(0, 1) else "less than "
            message += "...\n"
    else:
        message = '- no attribute has been defined for {} yet -'.format(
            element_name)

    return message


# def show_table_description(element_name):
#     message = 'The table {} can be categorized based on '.format(element_name)
#     category = resolver.extract_category(element_name)
#     if category:
#         message += '{}. '.format(category)
#     else:
#         message = 'There are no categories defined for the table {}'.format(element_name)
#     return message

# ------

# ------


def cleanhtml(raw_html):
    raw_html = raw_html.replace('<br />', '\n')
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def LIST_OF_ELEMENTS_FUNCTION(element):
    """
    DEPRECATED
    """
    show_column_list = resolver.extract_show_columns(element['element_name'])
    message = 'i. ' + ', '.join(x.upper() for x in show_column_list) + '\n'
    for i, e in enumerate(element['value']):
        message += '{}. '.format(i + 1)

        if show_column_list:
            message += ', '.join('{}'.format(e[x]) for x in show_column_list)

        if i != len(element['value']) - 1:
            message += '\n'
    return message
