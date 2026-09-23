from pydantic import BaseModel, Field
from enum import Enum

class CharacterEnum(str, Enum):
    ENGINEER = 'engineer'
    OPERATOR = 'operator'
    SHIFTLEADER = 'shiftleader'

class EditUser(BaseModel):
    username: str
    character: CharacterEnum | None = None