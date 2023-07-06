import contextlib
import copy
import dataclasses
import itertools
import logging
import re
import string
import typing
import warnings
from collections import namedtuple
from typing import Optional, Any

import pyodbc
from pypika import MySQLQuery as Query, Table, Criterion, Field, functions, \
    Order
from pypika.dialects import Dialects
from pypika.queries import QueryBuilder
from pypika.terms import Parameter

from chatidea.config import DatabaseSchema, DatabaseView
from chatidea.config.concept import Category
from chatidea.config.schema import TableSchema, Reference
from chatidea.config.view import TableView, ColumnView
from chatidea.database import resolver
from chatidea.settings import DB_NAME, DB_SCHEMA, DB_VIEW, \
    DB_USER, DB_PASSWORD, DB_HOST, QUERY_LIMIT, DB_DRIVER, DB_CHARSET

logger = logging.getLogger(__name__)

db_schema: Optional[DatabaseSchema] = DB_SCHEMA

db_view: Optional[DatabaseView] = DB_VIEW


def test_connection():
    logger.info('Database: %s', DB_NAME)
    logger.info('Testing connection with the database...')
    connection = _connect()
    logger.info('Connection succeeded! Closing connection...')
    connection.close()
    logger.info('Connection closed.')


class ConnectionStringBuilder:
    def __add_to_str(self, key: str, val: Any):
        self.parameters[key.upper()] = val

    def __init__(self, driver: str, server: str, database: str,
                 port: Optional[typing.Union[str, int]] = None):
        self.parameters = {}
        self.__add_to_str("driver", driver)
        self.__add_to_str("server", server)
        self.__add_to_str("database", database)
        if port:
            self.__add_to_str("port", port)

    def login(self, username: str,
              password: Optional[str] = None) -> "ConnectionStringBuilder":
        self.__add_to_str("UID", username)
        if password:
            self.__add_to_str("PWD", password)
        return self

    def authentication(self, auth: Optional[str]) -> "ConnectionStringBuilder":
        if auth:
            self.__add_to_str("authentication", auth)
        return self

    def charset(self, charset: Optional[str]) -> "ConnectionStringBuilder":
        if charset:
            self.__add_to_str("charset", charset)
        return self

    def __str__(self):
        return ";".join(f"{k}={v}" for k, v in self.parameters.items())

    def get_str(self) -> str:
        return str(self)


def _connect() -> pyodbc.Connection:
    connection_str = (ConnectionStringBuilder(DB_DRIVER, DB_HOST, DB_NAME)
                      .login(DB_USER, DB_PASSWORD)
                      .charset(DB_CHARSET)
                      .authentication("SqlPassword"))
    logger.debug("Connection string: %s", connection_str)
    connection = pyodbc.connect(connection_str.get_str())

    # MySQL-specific options for encoding issues
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    connection.setencoding(encoding='utf-8')
    return connection


@contextlib.contextmanager
def connect() -> pyodbc.Connection:
    connection = _connect()
    yield connection
    connection.close()


def execute_query(query: QueryBuilder,
                  parameters: Optional[tuple] = None,
                  connection: pyodbc.Connection = None,
                  limit: bool = True) -> list[pyodbc.Row]:
    # HERE FORCING THE LIMIT OF THE QUERY
    if limit and QUERY_LIMIT:
        if query.dialect == Dialects.MSSQL and 'ORDER BY' not in str(query):
            # When on MS SQL Server, the limit operation requires an ORDER BY
            # statement, so if the SQL does not contain one, we add it using
            # all the columns specified in the SELECT clause (in the same
            # order).
            cols = re.findall(r"SELECT (?:DISTINCT)? (.*?) FROM", str(query))
            cols = [x.split(query.QUOTE_CHAR)[1] for x in cols]
            query = query.orderby(*cols)
        query = query.limit(100)
    logger.info('Executing query: %s', query)
    if parameters:
        logger.info('Parameters tuple: {}'.format(parameters))
    if not connection:
        connection = _connect()
    cursor = connection.cursor()
    if parameters:
        cursor.execute(query.get_sql(), parameters)
    else:
        cursor.execute(query.get_sql())
    rows = cursor.fetchall()
    cursor.close()
    # FIXME: the function opens and closes a connection for each query. This
    #  feels like it's expensive: maybe we should have only a single connection
    #  that is opened when the server starts and is closed when the server is
    #  stopped
    if not connection:
        connection.close()
    return rows


def load_db_schema():
    # TODO: Remove global variable
    global db_schema
    db_schema = DB_SCHEMA


def load_db_view():
    global db_view
    db_view = DB_VIEW


def execute_query_select(query: str, params=None, limit=True) -> list[
    pyodbc.Row]:
    warnings.warn('This function is deprecated', DeprecationWarning)
    # HERE FORCING THE LIMIT OF THE QUERY
    if limit and QUERY_LIMIT:
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


class QueryDict(typing.TypedDict):
    q_string: str
    q_tuple: tuple


class Result(typing.TypedDict):
    query: QueryDict
    value: list[dict[str, Any]]
    real_value_length: int
    attributes: list[dict]


def get_dictionary_result(q_string, q_tuple, rows, cols, attributes) -> Result:
    query = {'q_string': q_string, 'q_tuple': q_tuple}

    value = list(map(lambda r: dict(zip(cols, r)), rows))

    return {'query': query,
            'value': value,
            'real_value_length': len(value),
            'attributes': attributes}


def get_table_schema_from_name(table_name: str) -> Optional[TableSchema]:
    return db_schema.get(table_name)  # may return None


def get_table_view_from_name(table_name: str) -> Optional[TableView]:
    return db_view.get(table_name)  # may return None


def get_references_from_name(table_name: str) -> list[Reference]:
    return db_schema.get(table_name).references


def query_show_attributes_examples(table: str, columns: list[str]):
    query = Query.from_(table).select(*columns).distinct().orderby(*columns)
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


Columns = typing.TypedDict('Columns', {'column': str, 'table': str})


def get_columns(table_name: str) -> list[Columns]:
    columns = [{'column': col, 'table': table_name} for col
               in get_table_schema_from_name(table_name).column_list]

    for fk in get_references_from_name(table_name):
        for col in columns:
            if fk.from_attribute == col['column']:
                col['column'] = fk.show_attribute
                col['table'] = fk.to_table
    return columns


def query_find(in_table_name, attributes):
    columns = get_columns(in_table_name)

    label_attributes(attributes, in_table_name)
    for a in attributes:
        a.setdefault('operator', '=')

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
                                 get_table_schema_from_name(
                                     in_table_name).column_list, attributes)


def query_join(element, relation):
    # the table is the last one of the last "by" in the relation
    to_table_name = relation.by[-1]['to_table_name']
    to_columns = get_columns(to_table_name)
    relation = relation.dict()

    # the table is the one of the first "by" in the relation
    from_table_name = relation['by'][0]['from_table_name']

    from_schema = get_table_schema_from_name(from_table_name)
    primary_columns = from_schema.primary_key_list

    relation['join_values'] = [element['value'][0][x] for x in primary_columns]
    relation['operator'] = '='
    relation['columns'] = primary_columns

    # HERE I REVERT THE RELATION to standardize with the attributes
    relation = get_reverse_relation(relation)

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
    rows = execute_query(query, tup)
    return get_dictionary_result(query.get_sql(), tup, rows,
                                 get_table_schema_from_name(to_table_name).column_list, [
                                     relation])  # mocking the relation as attribute


def get_reverse_relation(relation: dict):
    if 'by' not in relation:
        return relation

    final = copy.deepcopy(relation)
    final['by'].reverse()
    for r in final['by']:
        r['to_table_name'], r['from_table_name'] = \
            r['from_table_name'], r['to_table_name']
        r['to_columns'], r['from_columns'] = \
            r['from_columns'], r['to_columns']
    return final


def query_category(in_table_name, category) -> Result:
    columns = ("category", "count")
    ref: Optional[Reference] = None

    for fk in get_references_from_name(in_table_name):
        if fk.from_attribute == category.column:
            ref = fk

    from_table = Table(in_table_name)
    from_field = from_table.field(category.column)
    query: QueryBuilder = Query.from_(from_table)
    if ref:
        to_table = Table(ref.to_table)
        query = (query
                 .left_join(to_table)
                 .on(from_field == to_table.field(ref.to_attribute))
                 .select(to_table.field(ref.show_attribute), functions.Count('*'))
                 .groupby(from_field, to_table.field(ref.show_attribute))
                 .orderby(functions.Count('*'), order=Order.desc))
    else:
        query = (query
                 .select(from_field, functions.Count('*'))
                 .groupby(from_field)
                 .orderby(functions.Count('*'), order=Order.desc))

    tup = None
    rows = execute_query(query, tup, limit=False)
    return get_dictionary_result(str(query), tup, rows, columns, category)


def query_category_value(element_name, table_name, category_column: Category,
                         category_value):
    columns = get_columns(table_name)
    attribute = resolver.get_attribute_by_name(element_name,
                                               category_column.keyword).dict()
    attribute['value'] = category_value
    attribute['operator'] = 'LIKE'

    attributes = [attribute]
    label_attributes(attributes, table_name)

    tables = get_sql_tables([], table_name)
    where_category = get_WHERE_CATEGORY_query_string(table_name,
                                                     category_column.column)
    print(where_category)
    query: QueryBuilder = (Query.from_(tables.base)
                           .select(*get_sql_columns(columns))
                           .where(
        Criterion.all([where_category,
                       # get_WHERE_REFERENCE_query_string(table_name)
                       ]))
                           .orderby(*get_order_by([], table_name)))
    for table in tables.joins:
        query = query.left_join(table.target).on(table.on)
    val = str(category_value)
    val = '%' + val + '%'
    tup = tuple([val])

    rows = execute_query(query, tup)
    return get_dictionary_result(query.get_sql(), tup, rows,
                                 get_table_schema_from_name(
                                     table_name).column_list, attributes)


def simulate_view(table_name: str) -> list[ColumnView]:
    return get_table_view_from_name(table_name).column_list


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


def topological_sort(joins: list[Join]) -> list[Join]:
    nodes = set(x.who.get_table_name() for x in joins) | set(
        x.target.get_table_name() for x in joins)
    dependencies: dict[str, str] = {
        node: [x.target.get_table_name() for x in
               filter(lambda x: x.who.get_table_name() == node, joins)] for
        node in nodes
    }

    joins_by_starting: dict[str, Join] = {
        node: [x for x in
               filter(lambda x: x.who.get_table_name() == node, joins)] for
        node in nodes
    }

    permanent = set()
    temporary = set()
    none = set(nodes)

    final = []

    def visit(node):
        if node in permanent:
            return
        if node in temporary:
            raise ValueError("The graph has at least one cycle!")

        none.remove(node)
        temporary.add(node)
        for child in dependencies[node]:
            visit(child)

        temporary.remove(node)
        permanent.add(node)

        nonlocal final
        final = [node] + final

    while len(none | temporary) > 0:
        node = list(none)[0]
        visit(node)
    return list(itertools.chain(*[joins_by_starting[x] for x in final]))


def get_sql_tables(attributes,
                   table_name: Optional[str] = None) -> FromTables:
    JoinDef = namedtuple('JoinDef', ['start', 'end', 'from_attr', 'to_attr'])
    tab_string_list = []
    if table_name:
        tab_string_list.append(table_name)
    joins: set[JoinDef] = set()
    for a in attributes:
        for rel in (a.get('by', None) or []):
            for i in range(len(rel['from_columns'])):
                joins.add(JoinDef(rel['from_table_name'],
                                  rel['to_table_name'],
                                  rel["from_columns"][i],
                                  rel["to_columns"][i]))
    for fk in get_references_from_name(table_name):
        joins.add(JoinDef(table_name,
                          fk.to_table,
                          fk.from_attribute,
                          fk.to_attribute))
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

    return FromTables(Table(table_name), topological_sort(final_joins))


def get_WHERE_JOIN_query_string(attributes) -> list[Criterion]:
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


def get_WHERE_ATTRIBUTES_query_string(attributes,
                                      table_name=None,
                                      join=False) -> str:
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
            attr += " FROM " + get_sql_tables(attributes, table_name)
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
        other = Table(ref.to_table)
        from_att = this.field(ref.from_attribute)
        to_att = other.field(ref.to_attribute)
        ref_string_list.append(from_att == to_att)
    return ref_string_list
    # return " AND ".join(ref_string_list)


def get_WHERE_CATEGORY_query_string(table_name, category_column) -> Criterion:
    warnings.warn("This function is deprecated", DeprecationWarning)
    ret = Table(table_name).field(category_column)
    for fk in get_references_from_name(table_name):
        if fk.from_attribute == category_column:
            ret = Table(fk.to_table).field(fk.show_attribute)
    return ret.like(Parameter('?'))


def get_order_by(attributes: list[dict[str, str]], table: str) -> list[Field]:
    order_attrs = [a for a in attributes if a['keyword'] == 'order by']
    if not order_attrs:
        # If we do not have any keywords to order by, we'll simply order by
        # the attributes that we should show
        element_name = resolver.get_element_name_from_table_name(table)
        columns = resolver.extract_show_columns(element_name)[0].columns
        return [Table(table).field(col) for col in columns]

    return [Table(a['from_table']).field(a['value']) for a in order_attrs]


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    test_connection()
