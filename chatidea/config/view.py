from pydantic import BaseModel


class ColumnView(BaseModel):
    attribute: str
    display: str


class TableView(BaseModel):
    column_list: list[ColumnView]


class DatabaseView(BaseModel):
    __root__: dict[str, TableView]

    class Config:
        schema_extra = {
            '$id': "https://chatidea.gihub.io/chatidea/schemas/view.schema.json",
            'title': 'Database View',
            'description': 'A configuration object that allows to define how'
                           ' each table is presented to the user. It contains,'
                           ' for each table, a mapping between the name of the'
                           ' columns that should be shown as saved in the'
                           ' database and the name of the columns in "natural'
                           ' language".'
        }
