from typing import List, Union

from pydantic import BaseModel
from datetime import date, datetime, time, timedelta


class Content(BaseModel):
    created_at: datetime
    updated_at: datetime
    content: str
    #token_data: Union[dict, None] = None

class Contents(BaseModel):
    result: List[Content]
    count: int
    page: int
    limit: int
    total_pages: int