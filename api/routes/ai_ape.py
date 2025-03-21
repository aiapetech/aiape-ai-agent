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
    results =[]
    for record in mongo_result:
        if record["token_data"].get('token_details'):
            token_detail =  record["token_data"]['token_details']['data']
            record['token_img'] = token_detail['attributes']['image_url']
            record['token_name'] = token_detail['attributes']['name']
            record['token_symbol'] = token_detail['attributes']['symbol']
            record['token_address'] = token_detail['attributes']['address']
            record["gmgn_url"] = f"https://gmgn.ai/bsc/token/{record['token_address']}"
            record["dexscreener_url"] = f"https://dexscreener.com/bsc/{record['token_address']}"
            record["gmgn_bot_url"] = f"https://t.me/GMGN_sol_bot?start=i_BNKuCPoo"
        results.append(record)
       

    result = liquidity_bot_schema.Contents(
        result=results,
        count=mycol.count_documents({}),
        page=page,
        limit=limit,
        total_pages=mycol.count_documents({})//limit
    )

    return result
    
