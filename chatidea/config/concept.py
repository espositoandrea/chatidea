from typing import Literal, Optional

from pydantic import BaseModel


class ColumnDescriptor(BaseModel):
    keyword: str
    columns: list[str]


class Category(BaseModel):
    column: str
    alias: str
    keyword: str


class Reference(BaseModel):
    from_table_name: str
    from_columns: list[str]
    to_table_name: str
    to_columns: list[str]


class Attribute(BaseModel):
    keyword: str
    type: Literal["word"]
    columns: list[str]
    by: Optional[list[Reference]]


class Relation(BaseModel):
    keyword: str
    element_name: str
    by: list[Reference]


class Concept(BaseModel):
    element_name: str
    aliases: list[str]
    type: Literal["primary", "secondary", "crossable"]
    table_name: str
    show_columns: list[ColumnDescriptor]
    category: list[Category]
    attributes: list[Attribute]
    relations: list[Relation]


DatabaseConcepts = list[Concept]
