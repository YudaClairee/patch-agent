from pydantic import BaseModel, field_validator


class FeedbackCreate(BaseModel):
    instruction: str

    @field_validator("instruction", mode="before")
    @classmethod
    def trim_instruction(cls, v: str) -> str:
        return v.strip()

    @field_validator("instruction")
    @classmethod
    def validate_instruction(cls, v: str) -> str:
        if not v:
            raise ValueError("instruction must not be empty")
        if len(v) > 20000:
            raise ValueError("instruction must be at most 20000 characters")
        return v
