import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    twitterapi_io_api_key: str
    x_bearer_token: str
    openai_model: str
    tweet_limit: int
    output_dir: str


def load_settings() -> Settings:
    load_dotenv()

    twitterapi_io_api_key = os.getenv("TWITTERAPI_IO_API_KEY")
    x_bearer_token = os.getenv("X_BEARER_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")  
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    tweet_limit = int(os.getenv("TWEET_LIMIT", "50"))
    output_dir = os.getenv("OUTPUT_DIR", "./data")

    return Settings(
        twitterapi_io_api_key=twitterapi_io_api_key,
        x_bearer_token=x_bearer_token,
        openai_model=openai_model,
        tweet_limit=tweet_limit,
        output_dir=output_dir,
    )
