from typing import Optional, Iterator

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
