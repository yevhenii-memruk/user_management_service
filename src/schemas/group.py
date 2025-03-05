from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class GroupInDB(GroupBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupResponse(GroupInDB):
    pass
