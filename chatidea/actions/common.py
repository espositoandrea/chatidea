import functools
from typing import Callable

from chatidea import extractor
from chatidea.conversation import Context
from chatidea.patterns import Response
from chatidea.patterns.btn import Button

ActionReturn = tuple[list[str], list[Button]]
ActionFunction = Callable[[list[extractor.Entity], Context], ActionReturn]
Action = Callable[[list[extractor.Entity], Context], Response]


def action(func: ActionFunction):
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        response = Response()
        message, buttons = func(*args, **kwargs)
        if isinstance(message, str):
            response.add_message(message)
        else:
            response.add_messages(message)
        response.add_buttons(buttons)
        return response

    return wrapper


def add_to_context(name, entities, context):
    selected_element = dict()
    selected_element['value'] = "     "
    selected_element['entities'] = entities
    selected_element['query'] = None
    selected_element['real_value_length'] = 777
    selected_element['action_name'] = name
    selected_element['action_type'] = name
    selected_element['element_name'] = name
    context.append_element(selected_element)
