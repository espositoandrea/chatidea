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

import warnings
from typing import Optional, Iterator, Any

from pydantic import BaseModel, ConfigDict, RootModel


class ColumnView(BaseModel):
    attribute: str
    display: str

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class TableView(BaseModel):
    column_list: list[ColumnView]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class DatabaseView(RootModel):
    root: dict[str, TableView]
    model_config = ConfigDict(json_schema_extra={
        '$id': "https://chatidea.gihub.io/chatidea/schemas/view.schema.json",
        'title': 'Database View',
        'description': 'A configuration object that allows to define how'
                       ' each table is presented to the user. It contains,'
                       ' for each table, a mapping between the name of the'
                       ' columns that should be shown as saved in the'
                       ' database and the name of the columns in "natural'
                       ' language".'
    })

    def __iter__(self) -> Iterator[str]:
        return iter(self.root)

    def __getitem__(self, item) -> TableView:
        return self.root[item]

    def get(self, item, default=None) -> Optional[TableView]:
        return self.root.get(item, default)
