
import tweepy
import dotenv
import os,sys
sys.path.append(os.getcwd())
dotenv.load_dotenv()

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


# Example usage
if __name__ == "__main__":
    post_to_twitter("Hello, Twitter!")


    
