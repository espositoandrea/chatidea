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

from pydantic import BaseModel


class Reference(BaseModel):
    to_table: str
    from_attribute: str
    to_attribute: str
    show_attribute: str

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class TableSchema(BaseModel):
    column_list: list[str]
    primary_key_list: list[str]
    column_alias_list: Optional[dict[str, str]]
    references: list[Reference]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class DatabaseSchema(BaseModel):
    __root__: dict[str, TableSchema]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__root__)

    def __getitem__(self, item) -> TableSchema:
        return self.__root__[item]

    def get(self, item, default=None) -> Optional[TableSchema]:
        return self.__root__.get(item, default)

    class Config:
        schema_extra = {
            'title': 'Database Schema'
        }
