from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId


class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias='_id')
    project_id: str = Field(..., min_length=1)

    @classmethod
    @validator('project_id')
    def validate_project_id(cls, value:str):
        if not value.isalnum():
            raise ValueError('project_id has to be alphanumeric')
        # return super().validate(value)
        return value

    class Config:
        arbitrary_types_allowed = True
