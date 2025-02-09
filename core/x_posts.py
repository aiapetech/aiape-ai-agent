from apify_client import ApifyClient
import requests

def test():
    API_TOKEN = 'apify_api_tphFwXnlK4ZjIqKErblfavUoLekgVe3pYeid'
    params = {
      "offset":2,
      "limit": 10,
      "page": 2,
      "token": API_TOKEN,
    }
    url = f"https://api.apify.com/v2/acts/apidojo~twitter-scraper-lite/run-sync-get-dataset-items"
    list_of_run_url =f"https://api.apify.com/v2/acts/apidojo~twitter-scraper-lite/runs"
    last_run_item = "https://api.apify.com/v2/acts/apidojo~twitter-scraper-lite/runs/last/dataset/items"
    dataset_id = 'pA7P7fsChht0aBvPL'
    dataset_item_url= 'https://api.apify.com/v2/datasets/pA7P7fsChht0aBvPL/items'
    response = requests.get(url = dataset_item_url,params=params)
    pass



if __name__ == "__main__":  
    test()