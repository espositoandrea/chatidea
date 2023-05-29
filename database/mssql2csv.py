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

import argparse
import pathlib
from typing import Callable

import pandas as pd
from pypika import MSSQLQuery as Query, Schema, CustomFunction
from pypika.queries import QueryBuilder
from pypika.terms import PseudoColumn

from chatidea.database import broker as db


def setup_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Convert column information to JSON")
    parser.add_argument('outdir',
                        nargs='?',
                        type=pathlib.Path,
                        default=pathlib.Path('db-info'))
    return parser.parse_args()


# MS-SQL Server Schemas
information_schema = Schema("INFORMATION_SCHEMA")
sys = Schema("sys")

constraint_schema = PseudoColumn("CONSTRAINT_SCHEMA")
constraint_name = PseudoColumn("CONSTRAINT_NAME")

ObjectProperty = CustomFunction('OBJECTPROPERTY', ["object", "property"])
ObjectId = CustomFunction("OBJECT_ID", ["object"])
ObjectName = CustomFunction("OBJECT_NAME", ["object"])
QuoteName = CustomFunction("QUOTENAME", ["object"])
ColName = CustomFunction("COL_NAME", ["table", "column"])


def query(columns: list[str]):
    def wrapper(query_generator: Callable[[], QueryBuilder]):
        def inner():
            res = db.execute_query(query_generator(), limit=False)
            return pd.DataFrame.from_records(res, columns=columns)

        return inner

    return wrapper


@query(["TABLE_NAME", "COLUMN_NAME"])
def get_table_columns():
    return (Query.from_(information_schema.columns)
            .select("table_name", "column_name"))


@query(["TABLE_NAME", "PRIMARY_KEY"])
def get_primary_keys():
    return (Query.from_(information_schema.key_column_usage)
    .select("table_name", "column_name")
    .where(
        ObjectProperty(
            ObjectId(constraint_schema + "." + QuoteName(constraint_name)),
            "IsPrimaryKey").eq(1)
    ))


@query(["NAME", "FROM_TABLE", "FROM_ATTRIBUTE", "TO_TABLE", "TO_ATTRIBUTE"])
def get_foreign_keys():
    f = sys.foreign_keys
    fc = sys.foreign_key_columns
    return (Query.from_(f)
            .select(f.name,
                    ObjectName(f.parent_object_id).as_("table_name"),
                    ColName(fc.parent_object_id, fc.parent_column_id).as_(
                        "constraint_column_name"),
                    ObjectName(f.referenced_object_id).as_(
                        "referenced_object"),
                    ColName(fc.referenced_object_id,
                            fc.referenced_column_id).as_(
                        "referenced_column_name")
                    )
            .inner_join(fc)
            .on(f.object_id == fc.constraint_object_id)
            )


if __name__ == '__main__':
    args = setup_args()
    args.outdir.mkdir(exist_ok=True, parents=True)

    get_table_columns().to_csv(args.outdir / "columns.csv", index=False)
    get_primary_keys().to_csv(args.outdir / "primary-keys.csv", index=False)
    get_foreign_keys().to_csv(args.outdir / "foreign-keys.csv", index=False)
