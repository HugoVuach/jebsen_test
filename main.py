import argparse
import logging

from env_settings import load_settings
from x_scraper import XScraper
from event_classifier import LLM
from pipeline import execute_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline that retrieves tweets and transforms them into structured financial events via an LLM."
        )
    )
    parser.add_argument(
        "--username",
        type=str,
        default="financialjuice",
        help="X handle to analyze (without the @).",
    )
    parser.add_argument(
        "--max-tweets",
        type=int,
        help=(
            "Maximum number of tweets to retrieve. "
        ),
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = parse_args()
    settings = load_settings()

    max_tweets = args.max_tweets or settings.tweet_limit
    username = args.username.lstrip("@")

    twitter_client = XScraper(bearer_token=settings.x_bearer_token)
    llm_client = LLM(model=settings.openai_model)

    execute_pipeline(
        twitter_client=twitter_client,
        llm_client=llm_client,
        username=username,
        max_tweets=max_tweets,
        output_root=settings.output_dir,
    )


if __name__ == "__main__":
    main()
