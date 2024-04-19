"""
This module takes in input the mapping (concept) of the db and generates the chatito file
"""
import logging
import os
import sys
from functools import partial
from collections import Counter
from pprint import pprint
from typing import Any

import pypika


sys.path.insert(1, os.path.join(sys.path[0], '..'))
from chatidea.database.broker import execute_query
import yaml
from chatidea.database import resolver
from chatidea.settings import DialectQuery as Query
from pypika.queries import QueryBuilder, Table
import argparse
from chatidea.config.concept import Concept, Reference, Attribute


def setup_args():
    parser = argparse.ArgumentParser('Utility to check the database before training the model')
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


def flatten(l: list[list[Any]]) -> list[Any]:
    return [b for x in l for b in x]


def get_columns(table: Concept):
    return set(flatten(list(map(lambda x: x.columns, table.show_columns))) +
               flatten(list(map(lambda x: x.columns, filter(lambda x: not x.by, table.attributes)))) +
               list(map(lambda x: x.column, table.category)))

def test_attribute(attribute: Attribute, table: Concept, threshold=10):
    assert attribute.by is not None
    query: QueryBuilder = Query.from_(table.table_name).select(*[pypika.functions.Count(c) for c in attribute.columns])
    for rel in attribute.by:
        target = Table(rel.to_table_name)
        source = Table(rel.from_table_name)
        query = query.inner_join(target).on(target.field(rel.to_columns[0]) == source.field(rel.from_columns[0]))
    res = dict(zip(attribute.columns, execute_query(query)[0]))

    out = []
    for key, not_null in res.items():
        if not_null == 0:
            logging.error("No records for join-obtained %s (attribute keyword: %s)", key, attribute.keyword)
            out += ['ERROR']
        elif not_null <= threshold:
            logging.warning("Too few records for join-obtained %s (<= %d, attribute keyword: %s)", key, threshold, attribute.keyword)
            out += ['WARN']
        else:
            out+=["OK"]
    return out

def test_join_columns(table: Concept, threshold=10):
    partial_test_attribute=partial(test_attribute, table=table, threshold=threshold)
    l = flatten(list(map(partial_test_attribute, filter(lambda x: x.by, table.attributes))))
    return l
def test_simple_columns(column_name: str, table_name: str, threshold=10):
    table = Table(table_name)
    query: QueryBuilder = (Query.from_(table)
                           .select(pypika.functions.Count(table.field(column_name)))
                           .where(table.field(column_name).notnull())
                           )
    not_null = execute_query(query)[0][0]

    if not_null == 0:
        logging.error("No records for %s.%s", table_name, column_name)
        return 'ERROR'
    if not_null <= threshold:
        logging.warning("Too few records for %s.%s (<= %d)", table_name, column_name, threshold)
        return 'WARN'
    return "OK"

def check_table(table: Concept):
    logging.info("Checking table: %s", table.table_name)
    simple_columns = get_columns(table)
    test_table_simple_columns = partial(test_simple_columns, table_name=table.table_name)
    simple_errors = list(map(test_table_simple_columns, simple_columns))
    join_errors = test_join_columns(table)
    return simple_errors + join_errors
    # return []
    pass


if __name__ == "__main__":
    args = setup_args()

    resolver.load_db_concept()
    concepts = resolver.db_concept

    count = Counter(flatten(list(map(check_table, concepts))))
    print(" ----- Check complete -----")
    if count["WARN"] == 0 and count["ERROR"] == 0:
        print("Checks completed with no issues")
    elif count["ERROR"] == 0:
        print(f"Checks completed with {count['WARN']} warnings")
    elif count["WARN"] == 0:
        print(f"Checks completed with {count['ERROR']} errors")
        exit(1)
    else:
        print(f"Checks completed with {count['ERROR']} errors and {count['WARN']} warnings")
        exit(1)
