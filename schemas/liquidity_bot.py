from typing import List, Union

from pydantic import BaseModel
from datetime import date, datetime, time, timedelta


class Content(BaseModel):
    created_at: datetime
    updated_at: datetime
    content: str
    token_name:Union[str, None] = None
    token_symbol:Union[str, None] = None
    token_address:Union[str, None] = None
    token_img:Union[str, None] = None
    #token_data: Union[dict, None] = None
    gmgn_url: Union[str, None] = None
    dexscreener_url: Union[str, None] = None
    gmgn_bot_url: Union[str, None] = None

class Contents(BaseModel):
    result: List[Content]
    count: int
    page: int
    limit: int
    total_pages: int