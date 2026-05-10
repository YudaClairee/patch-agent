from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    instruction: str
