from . import actions
from . import meta
from .common import Action
from ..conversation import Context
from ..extractor import Entity
from ..patterns import nlu, Response

intents_to_action_functions: dict[str, Action] = {
    nlu.INTENT_HELP: meta.help,
    nlu.INTENT_START: meta.start,
    nlu.INTENT_HELP_ELEMENTS: meta.help_elements,
    nlu.INTENT_HELP_HISTORY: meta.help_history,
    nlu.INTENT_HELP_GO_BACK: meta.help_go_back,
    nlu.INTENT_MORE_INFO_FIND: actions.action_more_info_find,
    nlu.INTENT_MORE_INFO_FILTER: actions.action_more_info_filter,
    nlu.INTENT_FIND_ELEMENT_BY_ATTRIBUTE: actions.action_find_element_by_attribute,
    nlu.INTENT_FILTER_ELEMENT_BY_ATTRIBUTE: actions.action_filter_element_by_attribute,
    nlu.INTENT_CROSS_RELATION: actions.action_cross_relation,
    nlu.INTENT_SHOW_RELATIONS: actions.action_show_relations,
    nlu.INTENT_SHOW_MORE_ELEMENTS: actions.action_show_more_elements,
    nlu.INTENT_SHOW_LESS_ELEMENTS: actions.action_show_less_elements,
    nlu.INTENT_SELECT_ELEMENT_BY_POSITION: actions.action_select_element_by_position,
    nlu.INTENT_ORDER_BY: actions.action_order_by,
    nlu.INTENT_ORDER_BY_ATTRIBUTE: actions.action_order_by_attribute,
    nlu.INTENT_SHOW_MORE_EXAMPLES: actions.action_show_more_examples,
    nlu.INTENT_SHOW_MORE_EXAMPLES_ATTRIBUTE: actions.action_show_more_examples_attribute,
    # nlu.INTENT_SHOW_ATTRIBUTES_COMBINATIONS: action_show_attributes_combinations,
    nlu.VIEW_CONTEXT_ELEMENT: actions.action_view_context_element,
    nlu.INTENT_SHOW_CONTEXT: actions.action_show_context,
    nlu.INTENT_SHOW_MORE_CONTEXT: actions.action_show_more_context,
    nlu.INTENT_GO_BACK_TO_CONTEXT_POSITION: actions.action_go_back_to_context_position,
    nlu.INTENT_SHOW_TABLE_CATEGORIES: actions.action_show_table_categories,
    nlu.INTENT_AMBIGUITY_SOLVER: actions.action_ambiguity_solver,
    nlu.INTENT_FIND_ELEMENT_BY_CATEGORY: actions.action_find_element_by_category
}


def execute_action_from_intent_name(intent_name: str, entities: list[Entity], context: Context) -> Response:
    action_function = intents_to_action_functions.get(intent_name)
    if action_function:
        context.log('Calling action: {}'.format(action_function.__name__))
        response = action_function(entities, context)
    else:
        context.log('Executing fallback action')
        response = meta.fallback(entities, context)
    context.log('Response will be:\n'
                '\n'
                '{}\n'
                '\n'
                '- - - - - -'.format(response.get_printable_string()))

    return response
