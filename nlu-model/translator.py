"""
This module takes in input the mapping (concept) of the db and generates the chatito file
"""
import logging
import os
import re
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import yaml
from nltk.util import ngrams
from chatidea.database import resolver, broker
import argparse
from chatidea.database.broker import Query


def setup_args():
    parser = argparse.ArgumentParser('Generator for the chatito file')
    parser.add_argument('--template', '-t',
                        help="The template file",
                        type=argparse.FileType("r"),
                        dest="template_file",
                        default=sys.stdin)
    parser.add_argument("--params", '-p',
                        help="YAML file holding run parameters",
                        default=open("params.yaml"),
                        type=argparse.FileType("r"))
    parser.add_argument('--out', '-o',
                        help="The output file",
                        type=argparse.FileType("w"),
                        dest="model_file",
                        default=sys.stdout)
    args = parser.parse_args()
    args.params = yaml.safe_load(args.params)
    return args


if __name__ == "__main__":
    args = setup_args()
    MAX_NUMBER_OF_NGRAMS = args.params['dataset']['max_ngrams']

    resolver.load_db_concept()
    db_concept = resolver.db_concept

    broker.load_db_schema()
    broker.test_connection()

    whole_text_more_info_find = ""
    whole_text_more_info_filter = ""
    whole_text_find = ""
    whole_text_find_or = ""
    whole_text_filter = ""
    whole_text_and_or_el = ""
    whole_text_ambiguity_solver = ""
    whole_text_ambiguity_solver_words = "    "

    whole_element_text = ""
    whole_attribute_text = ""
    whole_example_type_text = ""
    whole_column_text = "@[el_columns]\n"

    idx_e = 1
    idx_e_alias = 0
    idx_tot = 0

    for e in db_concept:
        idx_tot += 1
        if e.type != 'primary':
            continue

        # aggiunta 10/03
        e_name = resolver.extract_element(e.element_name).table_name
        table_schema = broker.get_table_schema_from_name(e_name)
        all_columns_name = table_schema.column_list
        whole_column_text += "\n".join(
            f"    {c}" for c in all_columns_name) + "\n"
        if table_schema.column_alias_list:
            all_columns_name_alias = table_schema.column_alias_list
            for k, v in all_columns_name_alias.items():
                column_text = "    "
                column_text += v
                whole_column_text += column_text + "\n"
        # fine aggiunta

        whole_text_more_info_find += f"    ~[show?] ~[more_info_find] @[el_{idx_e}]\n"
        whole_text_more_info_filter += f"    ~[show?] ~[more_info_filter] @[el_{idx_e}]\n"
        whole_text_and_or_el += f"~[and_or_clause_el_{idx_e}]\n"

        element_text = f"@[el_{idx_e}]\n    "
        element_text += "\n    ".join(
            [e.element_name] + (e.aliases or []))
        whole_element_text += element_text + "\n\n"

        idx_e_alias += 1 + len(e.aliases or [])

        idx_a = 1
        for a in (e.attributes or []):
            idx_tot += 1
            # aggiunta 10/03
            if a.keyword:
                attribute_text = f"@[attr_{idx_e}_{idx_a}]\n" \
                                 f"    {a.keyword}"
                whole_attribute_text += attribute_text + "\n\n"

            example_type_text = f"@[{a.type}_{idx_e}_{idx_a}]\n"

            for col in (a.columns or []):
                query = (Query.from_(e.table_name
                                     if not a.by
                                     else a.by[-1].to_table_name)
                         .select(col)
                         .distinct())
                print(query)
                res = list(broker.execute_query(query))
                if res:
                    for r in res[:50]:  # max 50 examples each
                        if r[0]:
                            idx_tot += 1
                            string_word = str(r[0])
                            string_word = re.sub(r'[^a-zA-Z0-9]', ' ',
                                                 string_word)  # Replace all none alphanumeric characters with spaces
                            string_word = string_word.rstrip()
                            tokens = [token for token in
                                      string_word.split(" ") if
                                      token != ""]  # Break sentence in the token, remove empty tokens
                            if len(tokens) > 2:  # ngrams only string with more than 2 words
                                k = 0  # k is limitatore
                                for i in range(len(tokens), 0, -1):
                                    output = list(ngrams(tokens, i))
                                    k += 1
                                    for output_element in output:
                                        if k < MAX_NUMBER_OF_NGRAMS:
                                            output_list = list(
                                                output_element)
                                            words = output_list
                                            words[-1] = words[-1].rstrip(
                                                '\'\"-,.:;!?')
                                            example_type_text += "    " + " ".join(
                                                words).lower()
                                            example_type_text += "\n"

                            else:
                                try:
                                    words = string_word.split()
                                    words[-1] = words[-1].rstrip('\'\"-,.:;!?')
                                    example_type_text += "    " + " ".join(
                                        words).lower()
                                    example_type_text += "\n"
                                except IndexError:
                                    logging.error("%s %s %s", col,
                                                  e.table_name
                                                  if not a.by
                                                  else a.by[-1].to_table_name, r)
                                    # raise
            # fine aggiunta
            whole_example_type_text += example_type_text + "\n"
            # da qui
            text = ""

            if a.keyword:
                text += "@[attr_{}_{}] ".format(idx_e, idx_a)

                if a.type == 'num':  # use nlu.ENTITY_ATTR?
                    text += '@[op_num?] '

            text += "@[{}_{}_{}]".format(a.type, idx_e, idx_a)

            whole_text_find += "    ~[find] @[el_{}] ".format(
                idx_e) + text + " ~[and_or_clause_el_{}?]".format(
                idx_e) + " ~[order_by_clause?]" "\n"
            whole_text_filter += "    ~[filter] ~[those?] " + text + "\n"
            # aggiunta 10/03
            whole_text_and_or_el += "    " + "@[and] " + text + "\n"
            whole_text_and_or_el += "    " + "@[or] " + text + "\n"
            # fine aggiunta

            # single words training
            new_text = re.sub('@[attr_*[0-9]*_*[0-9]*]', '', text)
            new_text = new_text.replace(" ", "", 1)
            new_text += ("\n    ")
            whole_text_ambiguity_solver_words += new_text

            # a qui
            idx_a += 1
        whole_text_and_or_el += "\n"
        idx_e += 1

    idx_tot = min(idx_tot, 1200)  # max training set
    idx_e_alias = max(idx_e_alias, 100)

    #  prepending here...
    whole_text_and_or_el += "@[and]\n" + "    " + "and\n" + "\n@[or]\n" + "    " + "or\n"

    whole_text_more_info_find = "%[more_info_find]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_e_alias * 2 - idx_e_alias * 2 // 5, idx_e_alias * 2 // 5,
                whole_text_more_info_find)  # 1:4 proportion

    whole_text_more_info_filter = "%[more_info_filter]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_e_alias * 2 - idx_e_alias * 2 // 5, idx_e_alias * 2 // 5,
                whole_text_more_info_filter)  # 1:4 proportion

    whole_text_ambiguity_solver = whole_text_find

    whole_text_find = "%[find_el_by_attr]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_tot - idx_tot // 5, idx_tot // 5,
                whole_text_find)  # 1:4 proportion

    whole_text_filter = "%[filter_el_by_attr]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_tot - idx_tot // 5, idx_tot // 5,
                whole_text_filter)  # 1:4 proportion

    whole_text_ambiguity_solver = whole_text_ambiguity_solver.replace(
        "~[find]", "~[w_question?]")
    whole_text_ambiguity_solver += (
        re.sub('@[el_*[0-9]*]', '', whole_text_ambiguity_solver)).replace(
        "  @", " @")
    whole_text_ambiguity_solver = re.sub('and_or_clause_el_*[0-9]*', '',
                                         whole_text_ambiguity_solver).replace(
        " ~[?]", "")
    whole_text_ambiguity_solver = re.sub('order_by_clause', '',
                                         whole_text_ambiguity_solver).replace(
        " ~[?]", "")
    whole_text_ambiguity_solver += whole_text_ambiguity_solver_words[:-5]

    whole_text_ambiguity_solver = "%[ambiguity_solver_intent]('training': '{}', 'testing': '{}')\n{}" \
        .format(idx_tot - idx_tot // 5, idx_tot // 5,
                whole_text_ambiguity_solver).replace("\n    \n", "\n")

    final_text = "\n" + "\n".join(
        [whole_element_text, whole_column_text.lower(), whole_attribute_text,
         whole_example_type_text,
         whole_text_find, whole_text_and_or_el, whole_text_filter,
         whole_text_more_info_find, whole_text_more_info_filter,
         whole_text_ambiguity_solver])

    template = args.template_file.read()
    final_text = template + final_text
    args.model_file.write(final_text)
