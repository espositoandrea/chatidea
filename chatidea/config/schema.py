from typing import Optional

from pydantic import BaseModel


class Reference(BaseModel):
    to_table: str
    from_attribute: str
    to_attribute: str
    show_attribute: str


class TableSchema(BaseModel):
    column_list: list[str]
    primary_key_list: list[str]
    column_alias_list: Optional[dict[str, str]]
    references: list[Reference]


class DatabaseSchema(BaseModel):
    __root__: dict[str, TableSchema]

    class Config:
        schema_extra = {
            'title': 'Database Schema'
        }
