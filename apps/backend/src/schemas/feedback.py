from typing import Annotated

from pydantic import BaseModel, StringConstraints


class FeedbackCreate(BaseModel):
    instruction: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)
    ]
