from pydantic import BaseModel


class ColumnView(BaseModel):
    attribute: str
    display: str


class TableView(BaseModel):
    column_list: list[ColumnView]


DatabaseView = dict[str, TableView]
