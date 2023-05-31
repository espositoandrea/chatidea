from pydantic import BaseModel


class ColumnView(BaseModel):
    attribute: str
    display: str


class TableView(BaseModel):
    column_list: list[ColumnView]


class DatabaseView(BaseModel):
    __root__: dict[str, TableView]
