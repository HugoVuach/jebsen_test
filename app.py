# app2.py
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from env_settings import load_settings
from x_scraper import XScraper
from event_classifier import LLM
from pipeline import execute_pipeline


EVENT_TYPE_PRETTY = {
    "MACRO_DATA": "Macro data",
    "CENTRAL_BANK": "Central banks",
    "EARNINGS": "Earnings",
    "GEOPOLITICS": "Geopolitics",
    "CRYPTO": "Crypto",
    "COMMODITIES": "Commodities",
    "POLICY/REGULATION": "Policy & regulation",
    "OTHER": "Other",
}

IMPACT_ORDER = ["Faible", "Moyen", "Élevé"]



def load_latest_events_file(output_root: str) -> Tuple[Optional[Path], List[Dict]]:
    """
    Look into output_root/structured_events and return
    the most recent *_events.json file and its content as a list of dicts.
    """
    structured_dir = Path(output_root) / "structured_events"
    if not structured_dir.exists():
        return None, []

    files = sorted(structured_dir.glob("*_events.json"))
    if not files:
        return None, []

    latest = files[-1]
    try:
        with latest.open("r", encoding="utf-8") as f:
            events = json.load(f)
    except Exception:
        return latest, []

    return latest, events


def build_events_dataframe(events: List[Dict]) -> pd.DataFrame:
    """
    Convert raw events list into a cleaned pandas DataFrame
    with proper datetime parsing and extra helper columns.
    """
    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)

    if "tweet_created_at" in df.columns:
        df["tweet_created_at"] = pd.to_datetime(df["tweet_created_at"], errors="coerce")
        s = df["tweet_created_at"]
        try:
            s_no_tz = s.dt.tz_convert(None)
        except TypeError:
            s_no_tz = s
        df["tweet_created_at_display"] = s_no_tz.dt.strftime("%Y/%m/%d %H:%M:%S")

    if "tweet_created_at" in df.columns:
        df["tweet_date"] = df["tweet_created_at"].dt.date

    if "event_type" in df.columns:
        df["event_type_label"] = df["event_type"].map(EVENT_TYPE_PRETTY).fillna(df["event_type"])

    impact_size_map = {
        "Faible": 40.0,
        "Moyen": 80.0,
        "Élevé": 160.0,
    }
    if "impact" in df.columns:
        df["impact_size"] = df["impact"].map(impact_size_map).fillna(60.0)

    preferred_order = [
        "tweet_created_at",
        "tweet_created_at_display",
        "tweet_date",
        "event_type",
        "event_type_label",
        "country_region",
        "impact",
        "impact_size",
        "tweet_text",
        "explanation",
        "tweet_id",
    ]
    cols = [c for c in preferred_order if c in df.columns] + [
        c for c in df.columns if c not in preferred_order
    ]
    df = df[cols]

    return df



def main() -> None:
    st.set_page_config(
        page_title="FinancialJuice Event Explorer",
        layout="wide",
    )

    st.title("📈 FinancialJuice Tweets → Structured Financial Events")
    st.markdown(
        "This web UI runs the existing pipeline (tweets → LLM → events) and "
        "offers an enriched timeline with filters and a more readable display "
        "for non-technical users."
    )

    settings = load_settings()
    st.sidebar.header("⚙️ Pipeline settings")

    username = st.sidebar.text_input(
        "X username (without @)",
        value="financialjuice",
    )

    max_tweets = st.sidebar.number_input(
        "Maximum number of tweets to fetch",
        min_value=1,
        max_value=100,
        value=settings.tweet_limit,
        step=1,
    )

    st.sidebar.markdown("---")
    st.sidebar.write(f"Output directory: `{settings.output_dir}`")

    run_pipeline_button = st.sidebar.button("🚀 Run pipeline now")

    # Run pipeline if requested
    if run_pipeline_button:
        cleaned_username = username.lstrip("@").strip()
        if not cleaned_username:
            st.error("Please provide a valid X username.")
        else:
            st.info(
                f"Launching pipeline for `@{cleaned_username}` with "
                f"max_tweets={int(max_tweets)}..."
            )
            try:
                twitter_client = XScraper(bearer_token=settings.x_bearer_token)
                llm_client = LLM(model=settings.openai_model)

                with st.spinner("Fetching tweets and classifying them with the LLM..."):
                    execute_pipeline(
                        twitter_client=twitter_client,
                        llm_client=llm_client,
                        username=cleaned_username,
                        max_tweets=int(max_tweets),
                        output_root=settings.output_dir,
                    )

                st.success("✅ Pipeline completed. Latest results reloaded below.")
            except Exception as e:
                st.error(f"Error while running pipeline: {e}")

    st.markdown("---")

    latest_file, events = load_latest_events_file(settings.output_dir)

    if not events:
        st.warning(
            "No structured events found yet. "
            "Run the pipeline from the sidebar to generate some data."
        )
        return

    df = build_events_dataframe(events)

    if df.empty or "tweet_created_at" not in df.columns:
        st.warning("Events file loaded, but no valid `tweet_created_at` column was found.")
        return

    st.sidebar.header("🔍 Display filters")

    time_window = st.sidebar.selectbox(
        "Time range (relative to latest event)",
        [
            "All",
            "Last 30 minutes",
            "Last 1 hour",
            "Last 2 hours",
            "Last 24 hours",
            "Last 5 days",
        ],
    )

    unique_days = sorted(set(df["tweet_date"].dropna()))
    session_options = ["All days"] + [str(d) for d in unique_days]
    selected_session = st.sidebar.selectbox("Day / session", session_options)

    available_impacts = [imp for imp in IMPACT_ORDER if imp in df["impact"].unique()]
    selected_impacts = st.sidebar.multiselect(
        "Filter by impact",
        options=available_impacts,
        default=available_impacts,
    )

    if "event_type" in df.columns:
        existing_types = list(df["event_type"].dropna().unique())
        type_label_map = {
            code: EVENT_TYPE_PRETTY.get(code, code.title())
            for code in existing_types
        }
        ordered_codes = [
            code for code in EVENT_TYPE_PRETTY.keys() if code in type_label_map
        ]
        remaining_codes = [c for c in existing_types if c not in ordered_codes]
        ordered_codes += remaining_codes

        type_labels = [type_label_map[c] for c in ordered_codes]
        label_to_code = {label: code for code, label in type_label_map.items()}

        selected_type_labels = st.sidebar.multiselect(
            "Filter by event type",
            options=type_labels,
            default=type_labels,
        )

        selected_type_codes = [label_to_code[l] for l in selected_type_labels]
    else:
        selected_type_codes = None

    if "country_region" in df.columns:
        available_regions = sorted(df["country_region"].dropna().unique())
        selected_regions = st.sidebar.multiselect(
            "Filter by region",
            options=available_regions,
            default=available_regions,
        )
    else:
        selected_regions = None


    df_filtered = df.copy()
    max_time = df_filtered["tweet_created_at"].max()
    if pd.notnull(max_time) and time_window != "All":
        from datetime import timedelta

        if time_window == "Last 30 minutes":
            delta = timedelta(minutes=30)
        elif time_window == "Last 1 hour":
            delta = timedelta(hours=1)
        elif time_window == "Last 2 hours":
            delta = timedelta(hours=2)
        elif time_window == "Last 24 hours":
            delta = timedelta(days=1)
        elif time_window == "Last 5 days":
            delta = timedelta(days=5)
        else:
            delta = None

        if delta is not None:
            threshold = max_time - delta
            df_filtered = df_filtered[df_filtered["tweet_created_at"] >= threshold]

    if selected_session != "All days":
        from datetime import datetime as _dt
        try:
            selected_date = _dt.strptime(selected_session, "%Y-%m-%d").date()
            df_filtered = df_filtered[df_filtered["tweet_date"] == selected_date]
        except Exception:
            pass

    if selected_impacts:
        df_filtered = df_filtered[df_filtered["impact"].isin(selected_impacts)]

    if selected_type_codes is not None and selected_type_codes:
        df_filtered = df_filtered[df_filtered["event_type"].isin(selected_type_codes)]

    if selected_regions is not None and selected_regions:
        df_filtered = df_filtered[df_filtered["country_region"].isin(selected_regions)]

    if df_filtered.empty:
        st.warning("No events match the current filter selection.")
        return

    df_filtered = df_filtered.copy()
    jitter_seconds = np.random.uniform(-60, 60, size=len(df_filtered))
    df_filtered["tweet_created_at_jitter"] = df_filtered["tweet_created_at"] + pd.to_timedelta(
        jitter_seconds, unit="s"
    )


    st.subheader("🧭 Context")
    min_time = df_filtered["tweet_created_at"].min()
    max_time_filtered = df_filtered["tweet_created_at"].max()
    n_events = len(df_filtered)

    col_ctx1, col_ctx2, col_ctx3 = st.columns(3)

    with col_ctx1:
        st.markdown(f"**Account analyzed:** `@{username.lstrip('@')}`")
        if pd.notnull(min_time) and pd.notnull(max_time_filtered):
            st.markdown(
                "**Time span (after filters):** "
                f"{min_time.strftime('%Y/%m/%d %H:%M:%S')} → "
                f"{max_time_filtered.strftime('%Y/%m/%d %H:%M:%S')}"
            )
        st.markdown(f"**Number of events (filtered):** `{n_events}`")

    with col_ctx2:
        if "impact" in df_filtered.columns:
            high_impact = (df_filtered["impact"] == "Élevé").sum()
            medium_impact = (df_filtered["impact"] == "Moyen").sum()
            low_impact = (df_filtered["impact"] == "Faible").sum()
            st.markdown("**Impact breakdown:**")
            st.markdown(
                f"- 🔴 High impact: **{high_impact}**  \n"
                f"- 🟠 Medium impact: **{medium_impact}**  \n"
                f"- ⚪ Low impact: **{low_impact}**"
            )

    with col_ctx3:
        if "event_type_label" in df_filtered.columns:
            type_counts = (
                df_filtered["event_type_label"]
                .value_counts()
                .rename_axis("event_type_label")
                .reset_index(name="count")
            )
            st.markdown("**Top event types (filtered):**")
            for _, row in type_counts.head(5).iterrows():
                st.markdown(f"- **{row['event_type_label']}**: {row['count']}")

    st.markdown("---")


    st.subheader("⏱️ Timeline of events")

    color_scale = alt.Scale(
        domain=["Faible", "Moyen", "Élevé"],
        range=["#B0B0B0", "#FFC300", "#FF0000"],  # grey, yellow, red
    )

    size_scale = alt.Scale(domain=[40, 160], range=[40, 160])

    timeline_chart = (
        alt.Chart(df_filtered)
        .mark_circle(opacity=0.8)
        .encode(
            x=alt.X("tweet_created_at_jitter:T", title="Tweet time"),
            y=alt.Y("event_type_label:N", title="Event type"),
            color=alt.Color(
                "impact:N",
                title="Impact",
                scale=color_scale,
                sort=IMPACT_ORDER,
            ),
            size=alt.Size(
                "impact_size:Q",
                legend=None,
                scale=size_scale,
            ),
            tooltip=[
                alt.Tooltip(
                    "tweet_created_at:T",
                    title="Time",
                    format="%Y/%m/%d %H:%M:%S",
                ),
                alt.Tooltip("event_type_label:N", title="Event type"),
                alt.Tooltip("country_region:N", title="Region"),
                alt.Tooltip("impact:N", title="Impact"),
                alt.Tooltip("tweet_text:N", title="Tweet"),
                alt.Tooltip("explanation:N", title="LLM explanation"),
            ],
        )
        .properties(height=450)
    )

    st.altair_chart(timeline_chart, use_container_width=True)

    st.markdown("---")


    st.subheader("📋 Detailed events (filtered)")

    df_display = df_filtered.copy()

    if "tweet_created_at_display" in df_display.columns:
        if "tweet_created_at" in df_display.columns:
            df_display = df_display.drop(columns=["tweet_created_at"])
        df_display = df_display.rename(
            columns={"tweet_created_at_display": "tweet_created_at"}
        )

    cols_to_drop = [
        "tweet_date",
        "event_type",
        "impact_size",
        "tweet_text_short",        
        "tweet_id",
        "tweet_created_at_jitter",
    ]
    df_display = df_display.drop(
        columns=[c for c in cols_to_drop if c in df_display.columns],
        errors="ignore",
    )

    st.dataframe(df_display, use_container_width=True)

    st.caption(
        "You can sort the table by clicking on the column headers. "
        "Use the sidebar to adjust the time window, day/session, and filters "
        "by impact, event type, and region. "
        "Double-click on text cells to expand and view the full content."
    )



if __name__ == "__main__":
    main()
