from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    message: str


class Page(BaseModel):
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)
