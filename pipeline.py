import json
import logging
import os
from datetime import datetime
from typing import List, Dict

from x_scraper import XScraper
from event_classifier import LLM

logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> None:
    """Create the folder if it doesn't already exist"""
    os.makedirs(path, exist_ok=True)


def export_raw_tweets_json(tweets: List[Dict], 
                           output_dir: str, 
                           prefix: str,
                           ) -> str:
    """
    Save the raw tweets in JSON format    
    """
    ensure_directory(output_dir)
    json_path = os.path.join(output_dir, f"{prefix}_tweets_raw.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)

    logger.info("Raw tweets saved in : %s", json_path)
    return json_path


def export_events_json(events: List[Dict], 
                       output_dir: str, 
                       prefix: str,
                       ) -> str:
    """
    Save the structured events in JSON format.

    Each event contains:
      - tweet_id
      - tweet_created_at
      - tweet_text
      - event_type
      - country_region
      - impact
      - explanation
    """
    ensure_directory(output_dir)
    json_path = os.path.join(output_dir, f"{prefix}_events.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    logger.info("Structured events saved at: %s", json_path)
    return json_path


def execute_pipeline(twitter_client: XScraper,
                     llm_client: LLM,
                     username: str,
                     max_tweets: int,
                     output_root: str,
                     ) -> None:
    """
    Chaîne de traitement complète (JSON only) :

      1. Fetch latest original tweets for a given X account
      2. Serialize raw tweets to JSON
      3. Call the LLM (OpenAI) to turn each tweet into a structured event
      4. Serialize normalized events to JSON

    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = f"{username}_{timestamp}"

    raw_dir = os.path.join(output_root, "raw_tweets")
    structured_dir = os.path.join(output_root, "structured_events")

    # 1)  Collect tweets from X
    tweets = twitter_client.collect_tweets(
        username=username,
        max_tweets=max_tweets,
    )

    if not tweets:
        logger.warning("Aucun tweet récupéré pour @%s, arrêt de la pipeline.", username)
        return

    export_raw_tweets_json(tweets, raw_dir, prefix)

    # 2) LLM normalization
    logger.info("Starting LLM classification tweet by tweet...")
    events: List[Dict] = []

    for t in tweets:
        event = llm_client.classify_tweet(t["text"])

        events.append(
            {
                "tweet_id": t["id"],
                "tweet_created_at": t["created_at"],
                "tweet_text": t["text"],
                "event_type": event["event_type"],
                "country_region": event["country_region"],
                "impact": event["impact"],
                "explanation": event["explanation"],
            }
        )

    # 3) Output
    export_events_json(events, structured_dir, prefix)

    logger.info(
        "Pipeline completed for @%s. Number of events generated: %s",
        username,
        len(events),
    )
