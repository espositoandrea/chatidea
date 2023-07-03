from chatidea.actions.common import action, ActionReturn
from chatidea.conversation import Context
from chatidea.patterns import msg, btn
from .actions import add_to_context


@action
def fallback(entities, context: Context) -> ActionReturn:
    return [msg.ERROR], [
        btn.get_button_help_on_elements(),
        btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
        btn.get_button_history()
    ]


@action
def start(entities, context, add=True) -> ActionReturn:
    start_message = f"{msg.HI_THERE}\n{msg.element_names_examples()}"
    buttons = btn.get_buttons_tell_me_more()
    if add:
        add_to_context("start", entities, context)
    else:
        buttons += [
            btn.get_button_help_on_elements(),
            btn.get_button_go_back_to_context_position('- GO BACK! -', len(context.get_context_list()) - 1),
            btn.get_button_history()
        ]

    return [start_message], buttons


@action
def help(entities, context) -> ActionReturn:
    return ["For what do you need help?"], btn.get_buttons_help()


@action
def help_elements(entities, context):
    return [msg.element_names_examples()], btn.get_buttons_tell_me_more()


@action
def help_history(entities, context):
    return [msg.REMEMBER_HISTORY], btn.get_button_help_on_elements()


@action
def help_go_back(entities, context):
    return [msg.REMEMBER_GO_BACK], btn.get_button_help_on_elements()
