import json
import os,sys
sys.path.append(os.getcwd())
from core.db import engine as postgres_engine
from models.postgres_models import Tokens
from sqlmodel import Field, Session

def remove_id_field(file_path,new_file_name):
    with open(file_path, 'r') as file:
        data = json.load(file)
    new_data = []
    
    for item in data:
        del item['id']
        new_data.append(f"{item["symbol"]}, {item['name']}")
    
    with open(new_file_name, 'w') as file:
        json.dump(new_data, file, indent=4)
def remove_id_field(file_path,new_file_name):
    file_path = '/Users/jean/Work/SightSea-AI/demo/backend/app/list_of_project_cgc_full.json'
    new_file_name = 'list_of_project_cgc.json'
    remove_id_field(file_path,new_file_name)

def import_tokens():
    with open('cgc_data.json') as f:
        data = json.load(f)
    with Session(postgres_engine) as session:
        for item in data:
            token = Tokens(
                cgc_id=item['id'],
                symbol=item['symbol'], 
                name=item['name'],
                market_cap_rank=item['market_cap_rank'],
                search_text=f"{item['symbol'].lower()} {item['name'].lower()}")
            session.add(token)
        session.commit()
# Example usage
if __name__ == '__main__':
    import_tokens()