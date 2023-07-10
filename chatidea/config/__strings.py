from typing import Union

from pydantic import BaseModel, ConfigDict, Extra, RootModel


class InvariantString(BaseModel):
    invariant: str
    model_config = ConfigDict(extra=Extra.forbid)


class StringWithPlural(BaseModel):
    singular: str
    plural: str
    model_config = ConfigDict(extra=Extra.forbid)


# PluralizableString = Union[str, StringWithPlural, InvariantString]

class PluralizableString(RootModel):
    root: Union[str, StringWithPlural, InvariantString]

    def __eq__(self, other):
        return self.singular == other or self.plural == other

    @property
    def singular(self) -> str:
        if isinstance(self.root, str):
            return self.root
        elif isinstance(self.root, StringWithPlural):
            return self.root.singular
        return self.root.invariant

    @property
    def plural(self) -> str:
        if isinstance(self.root, str):
            return f"{self.root}s"
        elif isinstance(self.root, StringWithPlural):
            return self.root.plural
        return self.root.invariant
