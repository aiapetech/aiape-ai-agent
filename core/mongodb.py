import pymongo
from core.config import settings

def init_mongo():
    try:
        client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
        client.server_info() # force connection on a request as the
                            # connect=True parameter of MongoClient seems
                            # to be useless here 
    except pymongo.errors.ServerSelectionTimeoutError as err:
        # do whatever you need
        raise err
    return client