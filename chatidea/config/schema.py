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

from pydantic import BaseModel, RootModel, ConfigDict


class Reference(BaseModel):
    to_table: str
    to_attribute: str
    show_attribute: str

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class FullReference(Reference):
    from_column: str


class Column(BaseModel):
    name: str
    alias: Optional[str]
    primary_key: bool = False
    ref: Optional[Reference] = None


class TableSchema(BaseModel):
    column_list: list[Column]

    @property
    def primary_key_list(self) -> list[Column]:
        return [c for c in self.column_list if c.primary_key]

    @property
    def references(self) -> list[FullReference]:
        return [FullReference(**column.ref.model_dump(), from_column=column.name) for column in self.column_list if column.ref]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class DatabaseSchema(RootModel):
    root: dict[str, TableSchema]
    model_config = ConfigDict(json_schema_extra={
        'title': 'Database Schema'
    })

    def __iter__(self) -> Iterator[str]:
        return iter(self.root)

    def __getitem__(self, item) -> TableSchema:
        return self.root[item]

    def get(self, item, default=None) -> Optional[TableSchema]:
        return self.root.get(item, default)
