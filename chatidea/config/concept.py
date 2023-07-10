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
from typing import Literal, Optional, Iterator, Any

from pydantic import BaseModel, RootModel, ConfigDict

from chatidea.config.__strings import PluralizableString


class ColumnDescriptor(BaseModel):
    keyword: str
    columns: list[str]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class Category(BaseModel):
    column: str
    alias: PluralizableString
    keyword: str

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class Reference(BaseModel):
    from_table_name: str
    from_columns: list[str]
    to_table_name: str
    to_columns: list[str]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class Attribute(BaseModel):
    keyword: str
    order_by: bool = False
    type: Literal["word"]
    columns: list[str]
    by: Optional[list[Reference]] = None

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class Relation(BaseModel):
    keyword: str
    name: str
    by: list[Reference]

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class Concept(BaseModel):
    name: PluralizableString
    aliases: list[str] = []
    type: Literal["primary", "secondary", "crossable"]
    table_name: str
    show_columns: list[ColumnDescriptor] = []
    category: list[Category] = []
    attributes: list[Attribute] = []
    relations: list[Relation] = []

    def get_element_name(self, plural: bool = False) -> str:
        return self.name.plural if plural else self.name.singular

    @property
    def element_name(self) -> str:
        return self.get_element_name()

    def __getitem__(self, item: str) -> Any:
        warnings.warn('This function is deprecated', DeprecationWarning)
        return getattr(self, item)


class DatabaseConcepts(RootModel):
    root: list[Concept]
    model_config = ConfigDict(json_schema_extra={
        'title': 'Concepts List'
    })

    def __iter__(self) -> Iterator[Concept]:
        return iter(self.root)

    def __getitem__(self, item) -> Concept:
        return self.root[item]
