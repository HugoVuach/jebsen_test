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

* your **OpenAI API key** and chosen **model** (e.g. `gpt-4o-mini`)
* your **X** developer token
* default output directory and tweet limit if needed

Example:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

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


### 2. Visualize events with the Streamlit interface

Instead of using CLI scripts, you can explore the results through a simple web UI built with Streamlit:

```bash
streamlit run app.py
````

This will open a page in your browser (or give you a local URL to open manually).

**How to use the interface:**

* **Sidebar (on the left):**

  * Enter the X username you want to analyze (default: `financialjuice`, without the `@`).
  * Choose the maximum number of tweets to fetch.
  * Click on **“Run pipeline now”** to:

    * fetch the latest tweets from the selected account,
    * classify each tweet into a structured financial event using the LLM,
    * save the raw tweets and structured events to the `data/` folder,
    * refresh the visualizations on the page.

* **Main view:**

  * A **context panel** shows:

    * which account is being analyzed,
    * the time span covered by the filtered events,
    * how many events are currently displayed,
    * a quick breakdown by impact (high / medium / low).
  * A **timeline chart** displays each event over time:

    * Y-axis = Event type (e.g. *Macro data*, *Central banks*, *Policy & regulation*, …),
    * point color = Impact (red = high, yellow = medium, grey = low),
    * point size = Impact (larger points for higher impact),
    * hover any point to see the tweet text and the LLM explanation.
  * Below the chart, a **table of detailed events** lets you:

    * sort by clicking on column headers (time, type, region, impact, etc.),
    * scroll through the tweets and explanations.
    * double-click on text cells to expand and read the full content.

The filters in the sidebar (time range, day/session, impact, event type, region) can be combined to focus on the events that matter most for your use case.





## Design Choices

* The pipeline uses the **official X  Developer API** because, in practice, calls to `twitterapi.io` were regularly failing with `429 Too Many Requests` errors, even under the free tier, I don't know why.
* The output format is **JSON**, as it is easier to consume programmatically and avoids maintaining multiple representations.

---

## Possible Improvements

* Use a **paid / higher-tier API key** (X or a third-party provider) for tweet collection to avoid rate limits and improve robustness.
* Refine the **LLM prompt** and evaluate ex-post whether the `impact` classification aligns with realized market moves.
* Set up a WebSocket-based listener to ingest new tweets in real time and immediately run them through the LLM so events are detected and evaluated as soon as they appear.
