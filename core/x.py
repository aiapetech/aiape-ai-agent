
import tweepy
import dotenv
import os,sys
sys.path.append(os.getcwd())
dotenv.load_dotenv()

def post_to_twitter(tweet_text):
    # Authenticate to Twitter
    client_id = os.getenv("X_CLIENT_ID")
    client_secret = os.getenv("X_CLIENT_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    # client = tweepy.Client(consumer_key=client_id, consumer_secret=client_secret, access_token=access_token, access_token_secret=access_token_secret)
    # client.create_tweet(text=tweet_text)


    auth = tweepy.OAuth1UserHandler(
   client_id, client_secret,
   access_token, access_token_secret
)
    api = tweepy.API(auth)
    client = tweepy.Client(
    consumer_key=client_id,
    consumer_secret=client_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)


    try:
        # Create a tweet
        api.update_status(tweet_text)
        print("Tweet posted successfully!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


# Example usage
if __name__ == "__main__":
    post_to_twitter("Hello, Twitter!")


    