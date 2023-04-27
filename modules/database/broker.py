import copy
import dataclasses
import itertools
import json
import logging
import string
import warnings
from collections import namedtuple
from typing import Optional, Any

import pyodbc
from pypika import MySQLQuery as Query, Table, Criterion, Field
from pypika.queries import QueryBuilder
from pypika.terms import Parameter

from modules.database import resolver
from settings import DB_NAME, DB_SCHEMA_PATH, DB_VIEW_PATH, \
    DB_USER, DB_PASSWORD, DB_HOST, QUERY_LIMIT, DB_DRIVER, DB_CHARSET

logger = logging.getLogger(__name__)

db_schema: Optional[dict[str, Any]] = None

db_view: Optional[dict[str, Any]] = None


def test_connection():
    logger.info('Database: %s', DB_NAME)
    logger.info('Testing connection with the database...')
    connection = _connect()
    logger.info('Connection succeeded! Closing connection...')
    connection.close()
    logger.info('Connection closed.')


def _connect() -> pyodbc.Connection:
    connection = pyodbc.connect(f'DRIVER={DB_DRIVER};'
                                f'SERVER={DB_HOST};'
                                f'DATABASE={DB_NAME};'
                                f'UID={DB_USER};'
                                f'PWD={DB_PASSWORD};'
                                f'CHARSET={DB_CHARSET};')

    # MySQL-specific options for encoding issues
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    connection.setencoding(encoding='utf-8')
    return connection


def execute_query(query: QueryBuilder,
                  parameters: Optional[tuple] = None) -> list[pyodbc.Row]:
    # HERE FORCING THE LIMIT OF THE QUERY
    if QUERY_LIMIT:
        query = query.limit(100)
    logger.info('Executing query: %s', query)
    if parameters:
        logger.info('Parameters tuple: {}'.format(parameters))

    connection = _connect()
    cursor = connection.cursor()
    if parameters:
        cursor.execute(query.get_sql(), parameters)
    else:
        cursor.execute(query.get_sql())
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


def load_db_schema():
    logger.info('Database schema file: %s', DB_SCHEMA_PATH)
    logger.debug('Loading database schema file...')
    with open(DB_SCHEMA_PATH) as f:
        # TODO: Remove global variable
        global db_schema
        db_schema = json.load(f)
    logger.info('Database schema file has been loaded!')


def load_db_view():
    logger.info('Database view file: %s', DB_VIEW_PATH)
    logger.debug('Loading database view file...')
    with open(DB_VIEW_PATH) as f:
        # TODO: Remove global variable
        global db_view
        db_view = json.load(f)
    logger.info('Database view file has been loaded!')


def execute_query_select(query: str, params=None) -> list[pyodbc.Row]:
    warnings.warn('This function is deprecated', DeprecationWarning)
    # HERE FORCING THE LIMIT OF THE QUERY
    if QUERY_LIMIT:
        query += ' LIMIT 100'
    logger.info('Executing query: %s', query)
    if params:
        logger.info('Tuple: {}'.format(params))

    connection = _connect()
    cursor = connection.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


def get_dictionary_result(q_string, q_tuple, rows, cols, attributes) -> dict:
    query = {'q_string': q_string, 'q_tuple': q_tuple}

    value = list(map(lambda r: dict(zip(cols, r)), rows))

    return {'query': query,
            'value': value,
            'real_value_length': len(value),
            'attributes': attributes}


def get_table_schema_from_name(table_name: str) -> Optional[dict]:
    return db_schema.get(table_name)  # may return None


def get_table_view_from_name(table_name: str) -> Optional[dict]:
    return db_view.get(table_name)  # may return None


def get_references_from_name(table_name: str) -> list[dict]:
    return db_schema.get(table_name)['references']


def query_show_attributes_examples(table: str, columns: list[str]):
    query = Query.from_(table).select(*columns).distinct()
    rows = execute_query(query)
    return [r[0] for r in rows]


def decipher_attributes(attributes: list[dict]) -> \
        list[tuple[Criterion, str]]:
    flattened = [(Table(a["from_table"]).field(col), a['operator'],
                  a.get('value')) for a in attributes for col in
                 a["columns"]]

    def map_operators(field: Field, op: str) -> Criterion:
        if op == "LIKE":
            return field.like(Parameter("?"))
        elif op == "=":
            return field.eq(Parameter("?"))

    return [(map_operators(field, op), (f"%{v}%" if op == "LIKE" else v))
            for
            field, op, v in flattened]


def query_find(in_table_name, attributes):
    columns = []
    for col in get_table_schema_from_name(in_table_name)['column_list']:
        columns.append({'column': col, 'table': in_table_name})

    for fk in get_references_from_name(in_table_name):
        for col in columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    label_attributes(attributes, in_table_name)
    for a in attributes:
        if not a.get('operator'):
            a['operator'] = '='

    tables = get_sql_tables(attributes, in_table_name)
    columns = get_sql_columns(columns)
    order_by = get_order_by(attributes, in_table_name)
    where_conditions = decipher_attributes(attributes)

    query: QueryBuilder = (Query.from_(tables.base)
                           .select(*columns)
                           .orderby(*order_by)
                           .where(Criterion.any([x[0]
                                                 for x in where_conditions]))
                           .distinct())
    for x in tables.joins:
        query = query.join(x.target).on(x.on)
    tup = tuple(map(lambda x: x[1], where_conditions))
    rows = execute_query(query, tup)

    return get_dictionary_result(query.get_sql(), tup, rows,
                                 get_table_schema_from_name(in_table_name)[
                                     'column_list'], attributes)


def query_join(element, relation):
    to_table_name = relation['by'][-1][
        'to_table_name']  # the table is the last one of the last "by" in the relation

    to_schema = get_table_schema_from_name(to_table_name)

    to_columns = []
    for col in to_schema['column_list']:
        to_columns.append({'column': col, 'table': to_table_name})

    for fk in get_references_from_name(to_table_name):
        for col in to_columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    from_table_name = relation['by'][0][
        'from_table_name']  # the table is the one of the first "by" in the relation

    from_schema = get_table_schema_from_name(from_table_name)
    primary_columns = from_schema['primary_key_list']
    relation['join_values'] = [element['value'][0][x] for x in primary_columns]

    relation['operator'] = '='

    relation['columns'] = primary_columns

    relation = get_reverse_relation(copy.deepcopy(
        relation))  # HERE I REVERT THE RELATION to standardize with the attributes

    label_attributes([relation], from_table_name)

    tables = get_sql_tables([relation], to_table_name)
    columns = get_sql_columns(to_columns)
    where_conditions = [x[0] for x in decipher_attributes([relation])]

    query: QueryBuilder = (Query.from_(tables.base)
                           .select(*columns)
                           .where(Criterion.all(where_conditions))
                           .orderby(*get_order_by([], to_table_name))
                           .distinct())

    for x in tables.joins:
        query = query.join(x.target).on(x.on)

    tup = tuple(relation['join_values'])
    print(tup)
    rows = execute_query(query, tup)
    return get_dictionary_result(query.get_sql(), tup, rows,
                                 get_table_schema_from_name(to_table_name)[
                                     'column_list'], [
                                     relation])  # mocking the relation as attribute


def get_reverse_relation(relation):
    if relation.get('by'):
        relation['by'].reverse()  # reverting the list like a boss
        # here I swap like a boss
        for r in relation['by']:
            r['to_table_name'], r['from_table_name'] = r['from_table_name'], r[
                'to_table_name']
            r['to_columns'], r['from_columns'] = r['from_columns'], r[
                'to_columns']
    return relation


def query_category(in_table_name, category):
    columns = ("category", "count")
    ref = {}

    for fk in get_references_from_name(in_table_name):
        if fk['from_attribute'] == category:
            ref = fk

    if ref:
        query_string = "SELECT " + ref['to_table'] + "." + ref[
            'show_attribute'] + ", COUNT(*)"
        query_string += " FROM " + in_table_name + ", " + ref['to_table']
        query_string += " WHERE " + in_table_name + "." + category + " = " + \
                        ref['to_table'] + "." + ref['to_attribute']
        query_string += " GROUP BY " + in_table_name + "." + category
        query_string += " ORDER BY COUNT(*) DESC"
    else:
        query_string = "SELECT " + category + ", COUNT(*)"
        query_string += " FROM " + in_table_name
        query_string += " GROUP BY " + category
        query_string += " ORDER BY COUNT(*) DESC"

    print(query_string)
    tup = None
    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows, columns, category)


def query_category_value(element_name, table_name, category_column,
                         category_value):
    columns = []
    for col in get_table_schema_from_name(table_name)['column_list']:
        columns.append({'column': col, 'table': table_name})

    for fk in get_references_from_name(table_name):
        for col in columns:
            if fk['from_attribute'] == col['column']:
                col['column'] = fk['show_attribute']
                col['table'] = fk['to_table']

    attribute = resolver.get_attribute_by_name(element_name,
                                               category_column['keyword'])
    attribute['value'] = category_value
    attribute['operator'] = 'LIKE'

    attributes = [attribute]
    label_attributes(attributes, table_name)

    tables = get_sql_tables([], table_name)
    query: QueryBuilder = (Query.from_(tables.base)
                           .select(*get_sql_columns(columns))
                           .orderby(*get_order_by([], table_name)))
    query_string = query.get_sql() + " WHERE "
    where_ref_string = get_WHERE_REFERENCE_query_string(table_name)
    query_string += where_ref_string + " AND " if where_ref_string else ""
    query_string += get_WHERE_CATEGORY_query_string(table_name,
                                                    category_column['column'])
    print(query_string)

    val = str(category_value)
    val = '%' + val + '%'
    tup = tuple([val])
    print(tup)

    rows = execute_query_select(query_string, tup)
    return get_dictionary_result(query_string, tup, rows,
                                 get_table_schema_from_name(table_name)[
                                     'column_list'], attributes)


def simulate_view(table_name: str) -> list[dict[str, str]]:
    return get_table_view_from_name(table_name)['column_list']


# query helper

def label_attributes(attributes, table_name):
    num2alpha = dict(zip(range(1, 27), string.ascii_lowercase))
    i = 2  # the 'a' is taken by the first
    for a in attributes:
        if a.get('by'):
            for idx, rel in enumerate(a['by']):
                if not idx:
                    rel['from_letter'] = 'a'
                    rel['to_letter'] = num2alpha[i]
                else:
                    rel['from_letter'] = num2alpha[i]
                    rel['to_letter'] = num2alpha[i + 1]
                    i += 1
            a['letter'] = a['by'][-1]['to_letter']  # the last letter
            i += 1
            a['from_table'] = rel['to_table_name']
        else:
            a['from_table'] = table_name


# query creators

def get_sql_columns(columns) -> list[Field]:
    return [Table(col["table"]).field(col['column']) for col in columns]


@dataclasses.dataclass
class Join:
    who: Table
    target: Table
    on: Criterion


@dataclasses.dataclass
class FromTables:
    base: Optional[Table]
    joins: list[Join]


def get_sql_tables(attributes,
                   table_name: Optional[str] = None) -> FromTables:
    JoinDef = namedtuple('JoinDef', ['start', 'end', 'from_attr', 'to_attr'])
    tab_string_list = []
    if table_name:
        tab_string_list.append(table_name)
    joins: set[JoinDef] = set()
    for a in attributes:
        for rel in a.get('by', []):
            for i in range(len(rel['from_columns'])):
                joins.add(JoinDef(rel['from_table_name'],
                                  rel['to_table_name'],
                                  rel["from_columns"][i],
                                  rel["to_columns"][i]))
    for fk in get_references_from_name(table_name):
        joins.add(JoinDef(table_name,
                          fk['to_table'],
                          fk['from_attribute'],
                          fk['to_attribute']))
    joins: list[JoinDef] = sorted(joins, key=lambda x: (x.start, x.end))

    final_joins: list[Join] = []
    for _, b in itertools.groupby(joins, lambda x: (x.start, x.end)):
        b = list(b)
        final_joins.append(Join(Table(b[0].start),
                                Table(b[0].end),
                                Criterion.all([
                                    Table(x.start).field(x.from_attr) == Table(
                                        x.end).field(x.to_attr) for x in b
                                ])))

    return FromTables(Table(table_name), final_joins)


def get_WHERE_JOIN_query_string(attributes):
    warnings.warn('This function is deprecated', DeprecationWarning)
    join_string_list = []
    for a in attributes:
        for rel in a.get('by', []):
            # the lists must be equally long, obviously
            for i in range(len(rel['from_columns'])):
                join_string_list.append(
                    Table(rel["from_table_name"]).field(
                        rel["from_columns"][i]) == Table(
                        rel["to_table_name"]).field(rel["to_columns"][i]))
    return join_string_list
    # return " AND ".join(join_string_list)


def get_WHERE_ATTRIBUTES_query_string(attributes, table_name=None, join=False):
    warnings.warn("This function is deprecated", DeprecationWarning)
    attributes = [a for a in attributes if a['keyword'] != 'order by']
    attr_string_list = []
    already_in = []
    or_clause = False
    and_clause = False
    dec = decipher_attributes(attributes)
    for index, a in enumerate(attributes):
        if not or_clause:
            open_bracket = "( "
        else:
            open_bracket = " "
        or_clause = False
        and_clause = False
        attr = ""
        attr += " OR ".join(
            ["{}.{} {} ?".format(a['from_table'],  # not so pretty
                                 col,
                                 a['operator'])
             for col in a['columns']])
        if 'and_or' in a:
            if a['and_or'] == 'or':
                or_clause = True
                close_bracket = " OR"
            else:
                and_clause = True
                close_bracket = " )"
        else:
            close_bracket = " )"
        if index > 0 and 'and_or' in attributes[index - 1]:
            if attributes[index - 1]['and_or'] == 'or':
                prec_or_clause = True
        else:
            prec_or_clause = False
        if attr not in already_in or join or prec_or_clause:
            prec_or_clause = False
            already_in.append(attr)
            attr = open_bracket + attr + close_bracket
            if and_clause:
                attr += " AND"
            attr_string_list.append(attr)
        else:
            primary_key = get_table_schema_from_name(table_name)[
                'primary_key_list']
            primary_key_string = table_name + "." + primary_key[0]

            attr = "( "
            attr += primary_key_string
            attr += " IN ( SELECT DISTINCT " + primary_key_string
            attr += " FROM " + get_sql_tables(attributes,
                                              table_name)
            attr += " WHERE "
            where_join_string = get_WHERE_JOIN_query_string(attributes)
            attr += where_join_string + " AND " if where_join_string else ""
            attr += " OR ".join(
                ["{}.{} {} ?".format(a['from_table'], col, a['operator'])
                 for col in a['columns']])
            attr += " ) )"
            if 'and_or' in a:
                if a['and_or'] == 'or':
                    attr += " OR"
                else:
                    attr += " AND"
            attr_string_list.append(attr)
    return " ".join(attr_string_list)


def get_WHERE_REFERENCE_query_string(table_name) -> list[Criterion]:
    warnings.warn("This function is deprecated", DeprecationWarning)
    this = Table(table_name)
    ref_string_list = []
    for ref in get_references_from_name(table_name):
        other = Table(ref["to_table"])
        from_att = this.field(ref["from_attribute"])
        to_att = other.field(ref["to_attribute"])
        ref_string_list.append(from_att == to_att)
    return ref_string_list
    # return " AND ".join(ref_string_list)


def get_WHERE_CATEGORY_query_string(table_name, category_column):
    warnings.warn("This function is deprecated", DeprecationWarning)
    ret_string = '{}.{} LIKE ?'.format(table_name, category_column)
    for fk in get_references_from_name(table_name):
        if fk['from_attribute'] == category_column:
            ret_string = '{}.{} LIKE ?'.format(fk['to_table'],
                                               fk['show_attribute'])
    return ret_string


def get_order_by(attributes: list[dict[str, str]], table: str) -> list[Field]:
    order_attrs = [a for a in attributes if a['keyword'] == 'order by']
    if not order_attrs:
        # If we do not have any keywords to order by, we'll simply order by
        # the attributes that we should show
        element_name = resolver.get_element_name_from_table_name(table)
        columns = resolver.extract_show_columns(element_name)[0]['columns']
        return [Table(table).field(col) for col in columns]

    return [Table(a['from_table']).field(a['value']) for a in order_attrs]


if __name__ == '__main__':
    test_connection()
