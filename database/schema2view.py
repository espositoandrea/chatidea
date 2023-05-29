#! /usr/bin/env python3
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


def setup_args() -> argparse.Namespace:
    import sys
    parser = argparse.ArgumentParser("Convert JSON schema information to view")
    parser.add_argument("infile",
                        nargs='?',
                        type=argparse.FileType("r"),
                        default=sys.stdin)
    parser.add_argument('outfile',
                        nargs='?',
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    return parser.parse_args()


if __name__ == '__main__':
    args = setup_args()

    schema = json.load(args.infile)
    final = {
        table: {
            'column_list': [
                {"attribute": k, "display": k}
                for k in info['column_list']
            ]
        }
        for table, info in schema.items()
    }

    json.dump(final, args.outfile, indent=4)
