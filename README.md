# Pipeline: Turn FinancialJuice Tweets into Structured Financial Events with an LLM

This project fetches tweets from the X account `@financialjuice` and processes them through an LLM to produce structured financial events.

For each tweet, the pipeline extracts:

* the **event type**
* the **country/region**
* the **estimated market impact**
* a short **explanatory sentence**

The pipeline runs in three main stages:

---

## 1. Data Collection

* Uses the **X (Twitter) API v2** to fetch recent tweets from `@financialjuice`
* Keeps **only original tweets** (no retweets, no replies)
* Stores the **raw tweets as JSON** with the following fields:

  * `id`
  * `created_at`
  * `text`

---

## 2. LLM structuration

Each tweet is sent to an LLM (OpenAI) which returns a structured payload with:

  * `event_type` : `MACRO_DATA`, `CENTRAL_BANK`, `EARNINGS`, `GEOPOLITICS`,`CRYPTO`, `COMMODITIES`, `POLICY/REGULATION`, `OTHER`
  *  `country_region` : `US`, `EU`, `China`, `UK`, `Global`
  *  `impact` : `Faible`, `Moyen`, `Élevé`
  * `explanation` : A short explanation (1–2 sentences, in English) describing why this tweet might matter for markets.

The final structured event combines:

* tweet metadata: `tweet_id`, `tweet_created_at`, `tweet_text`
* LLM output: `event_type`, `country_region`, `impact`, `explanation`

---

## 3. Output & Visualization

* Structured events are saved as **JSON** in a dedicated output folder
* A small helper scripts (`visualize_events.py` and `generate_timeline.py`) can be used to:

  * group events by **event type**
  * display each event in the terminal with a color based on `impact` or in .png image with the timeline where:

    * **red** for `Élevé`
    * **yellow** for `Moyen`
    * **grey** for `Faible`

---

## Prerequisites

* **Python 3.10+** (3.11 recommended)
* An **X / Twitter Developer** account with API access (Bearer token)
* An **OpenAI** account with an API key

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file at the project root (based on `.env.example`) and fill in:

* your **OpenAI API key** and chosen **model** (e.g. `gpt-5-nano` or `gpt-4o-mini`)
* your **X** developer token
* default output directory and tweet limit if needed

Example:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

X_BEARER_TOKEN=...

OUTPUT_DIR=./data
TWEET_LIMIT=10
```

---

## How to Run the Pipeline

### 1. Run the main pipeline

```bash
python main.py --max-tweets 50
```

This will:

* fetch up to 50 recent original tweets from `@financialjuice`
* save raw tweets in `data/raw_tweets/`
* classify each tweet with the LLM
* save structured events in `data/structured_events/..._events.json`

### 2. Visualize the impact distribution

Once the events file has been generated, you can run:

```bash
python visualize_events.py
```

This script:

* loads the latest structured events JSON file
* groups events by `event_type`
* prints them in the terminal with a color based on `impact`
  (red = high, yellow = medium, grey = low)


```bash
python generate_timeline.py
```

This script loads the latest structured events and generates a `timeline_events.png` file, showing a time-based view of all events by type, with colors indicating impact (red = high, yellow = medium, grey = low).

---

## Design Choices

* The pipeline uses the **official X  Developer API** because, in practice, calls to `twitterapi.io` were regularly failing with `429 Too Many Requests` errors, even under the free tier, I don't know why.
* The output format is **JSON**, as it is easier to consume programmatically and avoids maintaining multiple representations.

---

## Possible Improvements

* Use a **paid / higher-tier API key** (X or a third-party provider) for tweet collection to avoid rate limits and improve robustness.
* Refine the **LLM prompt** and evaluate ex-post whether the `impact` classification aligns with realized market moves.
* Add richer visualizations
* Set up a WebSocket-based listener to ingest new tweets in real time and immediately run them through the LLM so events are detected and evaluated as soon as they appear.
