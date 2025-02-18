from datetime import datetime

from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
