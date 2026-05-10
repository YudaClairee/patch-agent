from pydantic import BaseModel, ConfigDict


class DiffFileRead(BaseModel):
    file_path: str
    status: str          # "added" | "removed" | "modified" | "renamed"
    additions: int
    deletions: int
    patch: str | None    # unified diff text

    model_config = ConfigDict(from_attributes=True)
