from pydantic import BaseModel, Field
from enum import Enum


class CharacterEnum(str, Enum):
    ENGINEER = "engineer"
    OPERATOR = "operator"
    SHIFTLEADER = "shiftleader"


class EditUser(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    character: CharacterEnum | None = None
