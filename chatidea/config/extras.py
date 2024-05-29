#  Copyright (C) 2023 andrea
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional

from pydantic import BaseModel


class ExtraConfiguration(BaseModel):
    greeting: Optional[str] = "Hello! I'm very happy to help you in exploring the database."
    help_history: Optional[str] = 'You can always check the history of the conversation, just ask!\n ' \
                                  'For instance you can try with: "show me the history" or maybe just "history".\n' \
                                  'I will help you to go back in the past, if you want, or just reset it completely.'
    help_go_back: Optional[str] = 'If you did something wrong, DON\'T PANIC!\n' \
                                  'By simply telling me something like "go back" or "undo" you can jump to the ' \
                                  'previous concepts of your history.\n' \
                                  'This might be a shortcut when you want to make little rollbacks, ' \
                                  'without accessing all your history.'
    error: Optional[str] = 'Sorry, I did not get that! :('
    finding_element: Optional[str] = 'Let me check...'
    nothing_found: Optional[str] = 'Nothing has been found, I am sorry!'
    one_result_found: Optional[str] = 'Et voilà! I found 1 result!'
    n_results_found_pattern: Optional[str] = 'Et voilà! I found {} results!'
    help_filter: Optional[str] = 'Remember that you can always filter them, click the button to get some hints'
    select_for_info_pattern: Optional[str] = 'Select the concept of type {} you are interested in.'
    introduce_element_to_show_pattern: Optional[str] = 'Here is what I know about this {}:'
    ambiguity_found: Optional[
        str] = 'I understand you want to search for something, maybe you can start from one of this questions.'
    empty_context_list: Optional[str] = 'I am sorry, but your conversation history is empty!'
    context_list_reset: Optional[str] = 'The history has been reset!'
    no_go_back: Optional[str] = 'You can not go back any further than that'
    remember_reset_history: Optional[str] = 'If you want you can reset the history of the conversation ' \
                                            'by clicking the reset button:'
