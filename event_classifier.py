import json
import logging
from typing import Dict
from openai import OpenAI  

logger = logging.getLogger(__name__)

EVENT_TYPES = [
    "MACRO_DATA",
    "CENTRAL_BANK",
    "EARNINGS",
    "GEOPOLITICS",
    "CRYPTO",
    "COMMODITIES",
    "POLICY/REGULATION",
    "OTHER",
]

COUNTRY_REGIONS = ["US", "EU", "China", "UK", "Global"]

IMPACTS = ["Faible", "Moyen", "Élevé"]


class LLM:
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI() 

    
    def _infer_event_from_tweet(self, tweet_text: str) -> Dict[str, str]:

        gpt_prompt = f"""
You are a senior financial news analyst.

Your goal is to map tweets into a single structured financial event.

Return ONLY a valid JSON object (no markdown, no backticks, no extra text)
with the following exact keys:

- "event_type": one of {EVENT_TYPES}
- "country_region": one of {COUNTRY_REGIONS}
- "impact": one of {IMPACTS}
- "explanation": 1–2 short sentences in English explaining how/why this tweet may matter for markets.

If the tweet is not clearly financial, use:
- event_type = "OTHER"
- country_region = "Global"
- impact = "Faible"
but still provide a short explanation in English.

Always output valid JSON, nothing else.
"""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": gpt_prompt},
                {"role": "user", "content": tweet_text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content
        logger.debug("LLM's response: %s", content)
        data = json.loads(content)

        event = {
            "event_type": data.get("event_type", "OTHER"),
            "country_region": data.get("country_region", "Global"),
            "impact": data.get("impact", "Faible"),
            "explanation": data.get("explanation","No explanation provided by the model.",),
        }

        # We enforce values within the allowed lists
        if event["event_type"] not in EVENT_TYPES:
            event["event_type"] = "OTHER"
        if event["country_region"] not in COUNTRY_REGIONS:
            event["country_region"] = "Global"
        if event["impact"] not in IMPACTS:
            event["impact"] = "Faible"

        return event


    def classify_tweet(self, tweet_text: str) -> Dict[str, str]:
        """
        Public method used by the pipeline.
        """
        logger.info("Classifying tweet using model %s", self.model)
        return self._infer_event_from_tweet(tweet_text)
