
import tweepy
import dotenv
import os,sys
sys.path.append(os.getcwd())
dotenv.load_dotenv()
from core.db import engine as postgres_engine
import pandas as pd


def post_to_twitter(tweet_text):
    # Authenticate to Twitter
    consumer_key = os.getenv("X_CONSUMER_KEY")
    consumer_secret = os.getenv("X_CONSUMER_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    # client = tweepy.Client(consumer_key=client_id, consumer_secret=client_secret, access_token=access_token, access_token_secret=access_token_secret)
    # client.create_tweet(text=tweet_text)
    client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)    
    try:
        # Create a tweet
        client.create_tweet(text=tweet_text)
        print("Tweet posted successfully!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def post_to_twitter_with_credentials(tweet_text, consumer_key, consumer_secret, access_token, access_token_secret, media_path=None):
    client_v2 = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)    

    try:
        # Create a tweet
        if media_path:
            auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
            auth.set_access_token(
                access_token,
                access_token_secret,
            )
            client_v1 = tweepy.API(auth)
            media = client_v1.media_upload(filename=media_path)
            media_id = media.media_id
            client_v2.create_tweet(text=tweet_text, media_ids=[media_id])
        else:
            client_v2.create_tweet(text=tweet_text)
        
        print("Tweet posted successfully!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def delete_tweet(tweet_id, consumer_key, consumer_secret, access_token, access_token_secret):
    client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)    
    try:
        # Delete a tweet
        client.delete_tweet(tweet_id)
        print("Tweet deleted successfully!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def list_profiles(consumer_key, consumer_secret, access_token, access_token_secret):
    client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)    
    try:
        # Delete a tweet
        res = client.get_me()
        print("Tweet deleted successfully!")
        return res
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
# Example usage
if __name__ == "__main__":
    failed_app = []
    tweet_text = """Reassessing the Concept of Altseason\n\nAccording to @ki_young_ju, the CEO of CryptoQuant, it’s time to rethink how we define Altseason. Traditionally, it has been understood as capital flowing from Bitcoin into altcoins, with Bitcoin Dominance serving as the primary metric.\n\nHowever, the introduction of ETFs has fundamentally shifted this dynamic. Bitcoin\'s capital is now "locked" within ETFs, meaning it no longer flows into altcoins as it once did.\n\nSo, what’s the new metric?\n\nIt\'s the trading volume of altcoins compared to that of Bitcoin.\n\nIn simpler terms:\n\nAltseason is now driven by stablecoin holders transitioning to altcoin investments. There\'s no longer a direct migration from Bitcoin; it has become somewhat isolated from the broader crypto market. According to the CEO of CryptoQuant, one of the leading blockchain data analysts, we\'ve just entered Altseason.\n\nWhat does "selective Altseason" mean?\n\nThe current capital flow is too fragmented, insufficient to propel all altcoins simultaneously. Instead, only a select few altcoins will experience significant growth, while others remain stagnant.\n\nThere\'s also another crucial change: the market now moves faster. You may have noticed this yourself—money rotates more swiftly, and sell-offs are more aggressive and decisive. This isn\'t a temporary phenomenon.\n\nThe market has become more efficient, and this efficiency won\'t change even if market conditions improve. Traders today are quicker, smarter, and more focused than ever.\n\nIn this environment, success hinges not just on making the right calls but on doing so swiftly. Stay vigilant; otherwise, you risk getting left behind."""
    df_twitter_credentials = pd.read_sql("SELECT * from twitter_credentials", postgres_engine)
    twitter_credentials = df_twitter_credentials.to_dict(orient='records')
    for i, twitter_credential in enumerate(twitter_credentials):
        #res = list_profiles(twitter_credential['consumer_key'], twitter_credential['consumer_secret'], twitter_credential['access_token'], twitter_credential['access_secret'])
        res = post_to_twitter_with_credentials(tweet_text, "AMBx6DzPBKB32ODYFoAP1LM22", "oPLnwzT60RO1OQoPwknLcClQdlBJIwPCLaIRY8ibdh7xA4g5aW", "1778311490061430784-bsAYwJgiI9gfGLpponf8L02cYSZE8l", "65EiZXhe6odLnMGkrdO0w7b2Y0qBSIdI3WphQtbm6kZXO")
        if res:
            print(twitter_credential["app_id"],res.data.username)
            
        else:
            print(f"Tweet posting with credentials {i} failed!")
            failed_app.append(twitter_credential['app_id'])

    # for i, twitter_credential in enumerate(twitter_credentials):
    #     res = post_to_twitter_with_credentials(tweet_text, twitter_credential['consumer_key'], twitter_credential['consumer_secret'], twitter_credential['access_token'], twitter_credential['access_secret'])
    #     if res:
    #         print(f"Tweet posted with credentials {i} successfully!")
            
    #     else:
    #         print(f"Tweet posting with credentials {i} failed!")
    #         failed_app.append(twitter_credential['app_id'])
    # pass

    
