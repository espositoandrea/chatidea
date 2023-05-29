#  Copyright (C) 2023 Andrea Esposito
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
import json
import pathlib

import pandas as pd


def setup_args() -> argparse.Namespace:
    import sys
    parser = argparse.ArgumentParser("Convert column information to JSON")
    parser.add_argument("indir",
                        nargs='?',
                        type=pathlib.Path,
                        default=pathlib.Path("db-info"))
    parser.add_argument('outfile',
                        nargs='?',
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    return parser.parse_args()


if __name__ == '__main__':
    args = setup_args()

    columns = pd.read_csv(args.indir / 'columns.csv').groupby("TABLE_NAME")
    keys = pd.read_csv(args.indir / 'primary-keys.csv').groupby("TABLE_NAME")
    fks = pd.read_csv(args.indir / 'foreign-keys.csv').groupby("FROM_TABLE")

    # columns.join(keys, on="TABLE_NAME")
    final = {
        table: {
            'column_list': list(infos['COLUMN_NAME']),
            'primary_key_list': (list(keys.get_group(table)["PRIMARY_KEY"])
                                 if table in keys.groups
                                 else list(infos['COLUMN_NAME'])),
            'references': [{
                "to_table": x["TO_TABLE"],
                "from_attribute": x["FROM_ATTRIBUTE"],
                "to_attribute": x["TO_ATTRIBUTE"],
                "show_attribute": None
            } for _, x in fks.get_group(table).iterrows()]
            if table in fks.groups else []
        }
        for table, infos in columns
    }
    json.dump(final, args.outfile, indent=4)
