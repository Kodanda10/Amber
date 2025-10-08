import tweepy
import os

class XClient:
    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token)

    def fetch_posts(self, leader_x_handle: str):
        user_response = self.client.get_user(username=leader_x_handle)
        if user_response.data:
            user_id = user_response.data.id
            tweets_response = self.client.get_users_tweets(id=user_id)
            if tweets_response.data:
                return [{"text": tweet.text} for tweet in tweets_response.data]
        return []