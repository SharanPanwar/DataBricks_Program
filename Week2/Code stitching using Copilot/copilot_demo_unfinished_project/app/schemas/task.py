from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
