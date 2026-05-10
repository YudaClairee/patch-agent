from typing import Literal
from pydantic import BaseModel, ConfigDict


class DiffFileRead(BaseModel):
    file_path: str
    status: Literal["added", "removed", "modified", "renamed"]
    additions: int
    deletions: int
    patch: str | None    

    model_config = ConfigDict(from_attributes=True)
