import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from  schemas import liquidity_bot as  liquidity_bot_schema
from core.mongodb import init_mongo
from datetime import datetime, timedelta
router = APIRouter(prefix="/liquidity-bot", tags=["AI Bot"])

mongo_client = init_mongo()
@router.get("/output/contents", response_model=liquidity_bot_schema.Contents)
def get_contents(
    duration:int = 1, time_unit:str = 'hour', page: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve contents.
    """
    mydb = mongo_client["sightsea"]
    mycol = mydb["liquidity_contents"]
    if time_unit == 'hour':
        mongo_result = mycol.find({"created_at": {"$gte": datetime.now() - timedelta(hours=duration)}}).sort([("created_at", -1)]).skip(page*limit).limit(limit)
    elif time_unit == 'day':
        mongo_result = mycol.find({"created_at": {"$gte": datetime.now() - timedelta(days=duration)}}).sort([("created_at", -1)]).skip(page*limit).limit(limit)
    elif time_unit == 'minute':
        mongo_result = mycol.find({"created_at": {"$gte": datetime.now() - timedelta(minutes=duration)}}).sort([("created_at", -1)]).skip(page*limit).limit(limit)
    else:
        mongo_result = mycol.find().sort([("created_at", -1)]).skip(page*limit).limit(limit)
    result = liquidity_bot_schema.Contents(
        result=list(mongo_result),
        count=mycol.count_documents({}),
        page=page,
        limit=limit,
        total_pages=mycol.count_documents({})//limit
    )

    return result
    
