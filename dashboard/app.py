"""
TruthStream AI — Streamlit Dashboard
======================================
A real-time fake-news analytics dashboard powered by FastAPI + GPT.

Pages:
  📊 Overview    — live stats, pie chart, timeline
  📰 Feed        — paginated article feed with labels
  🔍 Inspect     — select any article → get GPT explanation + summary
  ℹ️  About       — system architecture
"""
from __future__ import annotations

import os
import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTO_REFRESH_SECONDS = 30

st.set_page_config(
    page_title="TruthStream AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark, premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

/* FAKE badge */
.badge-fake {
    background: linear-gradient(135deg, #dc2626, #991b1b);
    color: white;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
/* REAL badge */
.badge-real {
    background: linear-gradient(135deg, #16a34a, #14532d);
    color: white;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Article card */
.article-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.article-card:hover { border-color: #60a5fa; }

/* GPT output */
.gpt-box {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border-left: 4px solid #6366f1;
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.25rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #e2e8f0;
    margin-top: 0.5rem;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #93c5fd;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_get(path: str, **params) -> dict | list | None:
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API error ({path}): {exc}")
        return None


def api_post(path: str, body: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{path}", json=body, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API error ({path}): {exc}")
        return None


def label_badge(label: str) -> str:
    cls = "badge-fake" if label == "Fake" else "badge-real"
    return f'<span class="{cls}">{label}</span>'


def conf_bar(conf: float, label: str) -> str:
    color = "#dc2626" if label == "Fake" else "#16a34a"
    pct = int(conf * 100)
    return (
        f'<div style="background:#334155;border-radius:999px;height:6px;width:100%;margin-top:4px">'
        f'<div style="background:{color};border-radius:999px;height:6px;width:{pct}%"></div>'
        f'</div><small style="color:#94a3b8">{pct}% confidence</small>'
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🔍 TruthStream AI")
    st.markdown("*Real-time fake news detector*")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Overview", "📰 Feed", "🔍 Inspect", "ℹ️ About"],
        label_visibility="collapsed",
    )
    st.divider()

    # Auto-refresh toggle
    auto_refresh = st.toggle("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.caption(f"Next refresh in ~{AUTO_REFRESH_SECONDS}s")

    st.markdown("---")
    st.caption(f"API: `{API_BASE}`")
    if st.button("🔄 Refresh now"):
        st.rerun()


# ---------------------------------------------------------------------------
# PAGE: Overview
# ---------------------------------------------------------------------------
if page == "📊 Overview":
    st.title("📊 Live Dashboard")

    stats = api_get("/stats")
    if not stats:
        st.stop()

    total = stats.get("total", 0)
    fake  = stats.get("fake", 0)
    real  = stats.get("real", 0)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📰 Total Articles", f"{total:,}")
    c2.metric("🔴 Fake News",   f"{fake:,}",  delta=f"{stats.get('fake_pct',0):.1f}%")
    c3.metric("🟢 Real News",   f"{real:,}",  delta=f"{stats.get('real_pct',0):.1f}%")
    c4.metric("🎯 Fake Rate",   f"{stats.get('fake_pct',0):.1f}%")

    st.divider()
    col_l, col_r = st.columns([1, 2])

    # Pie chart
    with col_l:
        st.markdown('<div class="section-header">Label Distribution</div>', unsafe_allow_html=True)
        if total:
            fig_pie = go.Figure(go.Pie(
                labels=["Fake", "Real"],
                values=[fake, real],
                hole=0.55,
                marker_colors=["#dc2626", "#16a34a"],
                textinfo="percent+label",
                hovertemplate="%{label}: %{value:,}<br>%{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=260,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No articles scored yet.")

    # Top sources bar chart
    with col_r:
        st.markdown('<div class="section-header">Top Sources by Volume</div>', unsafe_allow_html=True)
        sources = stats.get("top_sources", [])
        if sources:
            df_src = pd.DataFrame(sources)
            fig_bar = px.bar(
                df_src, x="count", y="source", orientation="h",
                color="count", color_continuous_scale="Blues",
                labels={"count": "Articles", "source": "Source"},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=0, r=10),
                height=260,
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No source data yet.")

    # Timeline
    st.divider()
    st.markdown('<div class="section-header">Articles Scored — Last 24 Hours</div>', unsafe_allow_html=True)
    timeline = api_get("/stats/timeline", hours=24)
    if timeline:
        df_tl = pd.DataFrame(timeline)
        if not df_tl.empty:
            fig_tl = go.Figure()
            fig_tl.add_trace(go.Bar(
                x=df_tl["hour"], y=df_tl.get("real", [0]*len(df_tl)),
                name="Real", marker_color="#16a34a",
            ))
            fig_tl.add_trace(go.Bar(
                x=df_tl["hour"], y=df_tl.get("fake", [0]*len(df_tl)),
                name="Fake", marker_color="#dc2626",
            ))
            fig_tl.update_layout(
                barmode="stack",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=10, b=10),
                height=280,
                xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155"),
            )
            st.plotly_chart(fig_tl, use_container_width=True)
        else:
            st.info("No timeline data for the last 24 hours.")
    else:
        st.info("Timeline data unavailable — articles may not have `scored_at` timestamps yet.")

    # Fake-rate by source table
    st.divider()
    st.markdown('<div class="section-header">Fake Rate by Source (min. 3 articles)</div>', unsafe_allow_html=True)
    fake_rate = stats.get("fake_rate_by_source", [])
    if fake_rate:
        df_fr = pd.DataFrame(fake_rate)
        df_fr["fake_rate_pct"] = (df_fr["fake_rate"] * 100).round(1).astype(str) + "%"
        st.dataframe(
            df_fr[["source", "total", "fake_count", "fake_rate_pct"]].rename(columns={
                "source": "Source",
                "total": "Total",
                "fake_count": "Fake",
                "fake_rate_pct": "Fake Rate",
            }),
            use_container_width=True,
            hide_index=True,
        )

    if auto_refresh:
        time.sleep(AUTO_REFRESH_SECONDS)
        st.rerun()


# ---------------------------------------------------------------------------
# PAGE: Feed
# ---------------------------------------------------------------------------
elif page == "📰 Feed":
    st.title("📰 Article Feed")

    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        label_filter = st.selectbox("Label", ["all", "Fake", "Real"])
    with col_f2:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col_f3:
        source_filter = st.text_input("Source filter (optional)", placeholder="e.g. newsapi")

    data = api_get(
        "/articles",
        label=label_filter,
        source=source_filter or "",
        page=page_num,
        page_size=20,
    )
    if not data:
        st.stop()

    articles_list = data.get("articles", [])
    total = data.get("total", 0)
    pages = data.get("pages", 1)

    st.caption(f"**{total:,}** articles found  ·  Page {page_num} of {pages}")
    st.divider()

    if not articles_list:
        st.info("No articles match the current filters.")
    else:
        for art in articles_list:
            lbl   = art.get("label", "Unknown")
            conf  = art.get("confidence", 0.0)
            title = art.get("title", "No title")
            src   = art.get("source", "")
            url   = art.get("url", "")
            pub   = art.get("published_at", "")[:10] if art.get("published_at") else ""

            st.markdown(
                f"""<div class="article-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="flex:1;margin-right:1rem">
                      <div style="font-weight:600;color:#f1f5f9;margin-bottom:6px">{title}</div>
                      <div style="color:#94a3b8;font-size:0.8rem">{src} &nbsp;·&nbsp; {pub}</div>
                    </div>
                    <div style="text-align:right;min-width:80px">
                      {label_badge(lbl)}
                      {conf_bar(conf, lbl)}
                    </div>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# PAGE: Inspect
# ---------------------------------------------------------------------------
elif page == "🔍 Inspect":
    st.title("🔍 Article Inspector")
    st.caption("Select an article to get a GPT explanation and summary.")

    # Load recent articles for selection
    data = api_get("/articles", label="all", page=1, page_size=50)
    if not data:
        st.stop()

    articles_list = data.get("articles", [])
    if not articles_list:
        st.info("No articles in database yet. Wait for the pipeline to process some.")
        st.stop()

    options = {
        f"[{a.get('label','?')}] {a.get('title','?')[:90]}": a
        for a in articles_list
    }
    selected_key = st.selectbox("Choose article", list(options.keys()))
    art = options[selected_key]

    lbl  = art.get("label", "Unknown")
    conf = art.get("confidence", 0.0)

    # Article detail card
    st.markdown(f"""
    <div class="article-card" style="margin-top:1rem">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span style="font-weight:700;font-size:1.05rem;color:#f1f5f9">{art.get('title','')}</span>
        {label_badge(lbl)}
      </div>
      <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:8px">
        📡 {art.get('source','')} &nbsp;·&nbsp; 📅 {str(art.get('published_at',''))[:10]}
        &nbsp;·&nbsp; 🎯 {int(conf*100)}% confidence
      </div>
      <div style="color:#cbd5e1;font-size:0.9rem;line-height:1.6">
        {art.get('content','')[:500]}{'...' if len(art.get('content','')) > 500 else ''}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    col_e, col_s = st.columns(2)

    # --- Explanation ---
    with col_e:
        st.markdown('<div class="section-header">🧠 GPT Explanation</div>', unsafe_allow_html=True)
        st.caption("Why was this classified as **" + lbl + "**?")

        if st.button("✨ Generate Explanation", key="btn_explain", type="primary"):
            with st.spinner("Asking GPT…"):
                result = api_post("/explain", {
                    "title":      art.get("title", ""),
                    "content":    art.get("content", ""),
                    "label":      lbl,
                    "confidence": conf,
                    "source":     art.get("source", ""),
                })
            if result:
                st.markdown(
                    f'<div class="gpt-box">{result["text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Model: `{result['model']}` · {result['tokens_used']} tokens")

    # --- Summary ---
    with col_s:
        st.markdown('<div class="section-header">📝 GPT Summary</div>', unsafe_allow_html=True)
        st.caption("Concise factual summary of the article.")

        if st.button("📄 Generate Summary", key="btn_summary"):
            with st.spinner("Asking GPT…"):
                result = api_post("/summarize", {
                    "title":      art.get("title", ""),
                    "content":    art.get("content", ""),
                    "label":      lbl,
                    "confidence": conf,
                    "source":     art.get("source", ""),
                })
            if result:
                st.markdown(
                    f'<div class="gpt-box">{result["text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Model: `{result['model']}` · {result['tokens_used']} tokens")

    # Raw JSON expander
    with st.expander("🔧 Raw article data (JSON)"):
        st.json(art)


# ---------------------------------------------------------------------------
# PAGE: About
# ---------------------------------------------------------------------------
elif page == "ℹ️ About":
    st.title("ℹ️ About TruthStream AI")

    st.markdown("""
    ## What is TruthStream AI?

    **TruthStream AI** is a real-time fake-news detection platform built as a graduation project
    to demonstrate Big Data architecture at scale.

    ---

    ## Architecture
    ```
    NewsAPI / GNews  →  Kafka (news.raw, 6 partitions)
                               │
                               ▼
                     Spark Structured Streaming
                       ├── clean_job   → Bronze / Silver Parquet
                       └── score_job   → RoBERTa UDF
                                            ├── Gold Parquet
                                            └── Kafka (news.scored)
                                                        │
                                                        ▼
                                                  mongo-sink
                                                        │
                                                        ▼
                                              MongoDB articles_scored
                                                        │
                                                        ▼
                                            ┌──────────────────────┐
                                            │  FastAPI Backend      │
                                            │  + OpenAI GPT layer   │
                                            └──────────┬───────────┘
                                                       │
                                                       ▼
                                            Streamlit Dashboard
    ```

    ---

    ## Tech Stack

    | Layer | Technology |
    |---|---|
    | Data Ingestion | NewsAPI, GNews → Kafka |
    | Stream Processing | Apache Spark Structured Streaming |
    | ML Classification | RoBERTa (hamzab/roberta-fake-news-classification) |
    | Data Storage | MongoDB + Parquet Data Lake |
    | API Backend | FastAPI + OpenAI GPT-4o-mini |
    | Dashboard | Streamlit |
    | Infrastructure | Docker Compose |

    ---

    ## Quick Links (while stack is running)

    | Service | URL |
    |---|---|
    | **This Dashboard** | http://localhost:8501 |
    | **API Docs (Swagger)** | http://localhost:8000/docs |
    | Spark Master UI | http://localhost:8090 |
    | Kafka UI | http://localhost:8080 |
    | Mongo Express | http://localhost:8081 |
    """)
