import logging
from typing import List, Dict
import requests

logger = logging.getLogger(__name__)


class XScraper:
    X_URL = "https://api.twitter.com/2"
    

    def __init__(self, bearer_token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {bearer_token}"})

    def get_user_id(self, username: str) -> str:
        """
        Retrieve a user's numeric ID from their @handle
        """
        url = f"{self.X_URL}/users/by/username/{username}"
        params = {"user.fields": "id"}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        user_id = data["data"]["id"]
        logger.info("User ID for @%s: %s", username, user_id)
        return user_id

    def collect_tweets(
        self,
        username: str,
        max_tweets: int,
    ) -> List[Dict]:
        """
        Retrieve a user's recent tweets (excluding retweets and replies). Return a list of dicts with id, created_at, text.
        """
        user_id = self.get_user_id(username)
        api_max_results = max(5, min(max_tweets, 100))
        url = f"{self.X_URL}/users/{user_id}/tweets"
        params = {"max_results": api_max_results, "exclude": "retweets,replies", "tweet.fields": "created_at"}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tweets = []
        
        for twt in data.get("data", []):
            tweets.append(
                {
                    "id": twt["id"],
                    "created_at": twt["created_at"],
                    "text": twt["text"],
                }
            )

        logger.info("Number of tweets retrieved: %s", len(tweets))
        return tweets
