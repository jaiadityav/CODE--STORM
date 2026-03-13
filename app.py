"""
app.py — ReturnIQ: Why Are Customers Returning My Product?
Fully upgraded to meet all problem statement requirements:
  ✅ Focus on 1–3 star reviews
  ✅ LLM clustering (sentence-transformers + KMeans)
  ✅ Visual charts of complaint categories
  ✅ "38% say X → do Y" insight format
  ✅ Listing comparison table
  ✅ Paste link → full returns intelligence report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from modules.data_collector import collect_all
from modules.text_cleaning import preprocess_reviews
from modules.sentiment_analysis import analyze_batch, get_sentiment_summary
from modules.complaint_detection import detect_themes, extract_keywords, get_cluster_summary, filter_low_star
from modules.recommendation_engine import generate_recommendations, generate_health_score, generate_top_insight

st.set_page_config(
    page_title="ReturnIQ — Why Are Customers Returning My Product?",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_COLORS = {
    "Sizing / Fit Issue":    "#f59e0b",
    "Product Quality":       "#ef4444",
    "Misleading Listing":    "#ec4899",
    "Packaging Issue":       "#8b5cf6",
    "Delivery / Logistics":  "#3b82f6",
    "Customer Service":      "#06b6d4",
    "Price / Value":         "#10b981",
    "Missing Parts":         "#6b7280",
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background-color:#0f0f15;}
.stApp *,.stMarkdown *,p,li,span,div,label{color:#e2e8f0 !important;}
h1,h2,h3,h4{color:#ffffff !important;}

.hero-title{font-size:2.5rem;font-weight:900;color:#fff !important;line-height:1.1;margin-bottom:6px;}
.hero-accent{color:#ff4d6d !important;}
.hero-sub{color:#94a3b8 !important;font-size:0.94rem;line-height:1.6;margin-bottom:14px;}
.hero-pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;}
.pill{padding:3px 12px;border-radius:20px;font-size:0.7rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;border:1px solid;}
.p-red{background:rgba(255,77,109,.12);color:#ff4d6d !important;border-color:#ff4d6d;}
.p-blue{background:rgba(77,159,255,.12);color:#4d9fff !important;border-color:#4d9fff;}
.p-green{background:rgba(77,255,166,.12);color:#4dffa6 !important;border-color:#4dffa6;}
.p-purple{background:rgba(167,139,250,.12);color:#a78bfa !important;border-color:#a78bfa;}

.insight-banner{background:linear-gradient(135deg,#1a0a2e,#0a1628);border:1px solid #4c1d95;
  border-left:4px solid #a78bfa;border-radius:12px;padding:20px 24px;margin:18px 0;}
.insight-label{font-size:.68rem;text-transform:uppercase;letter-spacing:1px;
  color:#a78bfa !important;font-weight:700;margin-bottom:8px;}
.insight-text{font-size:1.04rem;color:#e2e8f0 !important;line-height:1.65;font-weight:500;}

.metric-card{background:#1a1a24;border:1px solid #2a2a3a;border-radius:12px;padding:18px;text-align:center;}
.metric-value{font-size:2rem;font-weight:800;}
.metric-label{font-size:.68rem;color:#94a3b8 !important;text-transform:uppercase;letter-spacing:.08em;margin-top:4px;}

.source-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;margin:2px;}
.badge-amazon{background:#ff990022;color:#ff9900 !important;border:1px solid #ff9900;}
.badge-flipkart{background:#2874f022;color:#7ab4ff !important;border:1px solid #2874f0;}
.badge-reddit{background:#ff450022;color:#ff6314 !important;border:1px solid #ff4500;}
.badge-youtube{background:#ff000022;color:#ff6666 !important;border:1px solid #ff0000;}
.badge-google_shopping{background:#4dffa622;color:#4dffa6 !important;border:1px solid #4dffa6;}
.badge-twitter{background:#1d9bf022;color:#1d9bf0 !important;border:1px solid #1d9bf0;}

.sec-title{font-size:.7rem;text-transform:uppercase;letter-spacing:1px;color:#6b7280 !important;
  font-weight:600;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #1e1e2e;}

.cluster-card{background:#1a1a24;border:1px solid #2a2a3a;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.kw-tag{display:inline-block;background:rgba(167,139,250,.12);border:1px solid #a78bfa;
  color:#c4b5fd !important;padding:2px 9px;border-radius:20px;font-size:.7rem;margin:2px;}

.rec-card{background:#1a1a24;border:1px solid #2a2a3a;border-radius:12px;padding:18px 22px;margin-bottom:12px;}
.rec-card-HIGH{border-left:4px solid #ef4444;}
.rec-card-MEDIUM{border-left:4px solid #f59e0b;}
.rec-card-LOW{border-left:4px solid #22c55e;}
.rec-insight{font-size:.87rem;color:#cbd5e1 !important;line-height:1.6;margin-bottom:12px;
  padding:9px 13px;background:rgba(255,255,255,.04);border-radius:8px;border-left:3px solid #a78bfa;}
.rec-action{font-size:.87rem;color:#e2e8f0 !important;padding:6px 0;border-bottom:1px solid #2a2a3a;}
.rec-action:last-child{border-bottom:none;}

.rev-card{background:#1a1a24;border:1px solid #2a2a3a;border-radius:10px;padding:13px 16px;margin-bottom:8px;}
.rev-card-neg{border-left:3px solid #ef4444;}
.rev-card-neu{border-left:3px solid #6366f1;}
.rev-text{font-size:.86rem;color:#cbd5e1 !important;line-height:1.6;margin-bottom:8px;}
.rev-badge{font-size:.7rem;padding:2px 8px;border-radius:12px;font-weight:600;margin-right:4px;}
.rb-neg{background:rgba(239,68,68,.15);color:#f87171 !important;}
.rb-neu{background:rgba(99,102,241,.15);color:#a5b4fc !important;}
.rb-src{background:rgba(107,114,128,.15);color:#9ca3af !important;font-family:monospace;}
.rb-star{background:rgba(245,158,11,.15);color:#fbbf24 !important;}
.pb-high{background:rgba(239,68,68,.15);color:#f87171 !important;padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:700;}
.pb-medium{background:rgba(245,158,11,.15);color:#fbbf24 !important;padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:700;}
.pb-low{background:rgba(34,197,94,.15);color:#4ade80 !important;padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:700;}

div[data-testid="stButton"] button{background:#ff4d6d !important;color:white !important;
  border:none !important;border-radius:8px !important;font-weight:700 !important;
  font-size:1rem !important;width:100% !important;padding:.6rem 1.5rem !important;}
.stTextInput input{background:#1a1a24 !important;border:1px solid #3a3a4a !important;
  color:white !important;border-radius:8px !important;font-size:1rem !important;padding:12px !important;}
.stTextInput input::placeholder{color:#555 !important;}
section[data-testid="stSidebar"]{background:#111118 !important;}
section[data-testid="stSidebar"] *{color:#e2e8f0 !important;}
</style>
""", unsafe_allow_html=True)


def _dark(h=320, **kw):
    d = dict(paper_bgcolor="rgba(26,26,36,1)", plot_bgcolor="rgba(26,26,36,1)",
             font=dict(family="Inter,sans-serif", color="#e2e8f0", size=12),
             margin=dict(t=16, b=16, l=0, r=60), height=h)
    d.update(kw)
    return d


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")
    max_pages    = st.slider("Pages to scrape", 1, 5, 3)
    use_reddit   = st.checkbox("Reddit (free, no key)", value=True)
    use_google   = st.checkbox("Google Shopping (free, no key)", value=True)
    st.markdown("---")
    st.markdown("**Optional API Keys**")
    st.caption("YouTube gives 20× more reviews")
    youtube_key    = st.text_input("YouTube API Key",       type="password", placeholder="AIzaSy...")
    twitter_token  = st.text_input("Twitter Bearer Token",  type="password", placeholder="AAAA...")
    with st.expander("How to get free API keys?"):
        st.markdown("""
**YouTube (Free — 10k/day):**
1. console.cloud.google.com
2. New Project → Enable YouTube Data API v3
3. Credentials → API Key → copy here

**Twitter/X (Free):**
1. developer.twitter.com → Create App
2. Copy Bearer Token here
        """)
    st.markdown("---")
    st.caption("Paste a link → AI scrapes reviews → LLM clusters 1–3 star reviews → actionable fix plan.")


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-title'>Why are customers <span class='hero-accent'>returning</span> your product?</div>
<div class='hero-sub'>Paste any Amazon or Flipkart link. AI scrapes reviews, runs LLM clustering on
1–3 star reviews, and delivers a prioritized fix plan.</div>
<div class='hero-pills'>
  <span class='pill p-red'>Sentiment Analysis</span>
  <span class='pill p-blue'>LLM Pattern Detection</span>
  <span class='pill p-green'>1–3 Star Focus</span>
  <span class='pill p-purple'>Actionable Insights</span>
</div>
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    user_input = st.text_input(label="url",
        placeholder="https://www.amazon.in/...  or  https://www.flipkart.com/...  or  product name",
        label_visibility="collapsed")
with col_btn:
    analyze_clicked = st.button("Analyze →")


# ── MAIN ANALYSIS ─────────────────────────────────────────────────────────────
def run_analysis(raw_reviews: list, product_name: str, sources: dict):
    if not raw_reviews:
        st.error("No reviews collected.")
        return

    with st.spinner("Cleaning text..."):
        reviews = preprocess_reviews(raw_reviews)
    if not reviews:
        st.error("All reviews filtered out after cleaning.")
        return

    with st.spinner("Analyzing sentiment..."):
        reviews = analyze_batch(reviews)
        sentiment = get_sentiment_summary(reviews)

    with st.spinner("Running LLM clustering on 1–3 star reviews..."):
        themes   = detect_themes(reviews)
        keywords = extract_keywords(reviews)
        clusters = get_cluster_summary(reviews)

    recs        = generate_recommendations(themes)
    health      = generate_health_score(sentiment)
    top_insight = generate_top_insight(themes, product_name)
    low_star_n  = len(filter_low_star(reviews))

    # ── 1. TOP INSIGHT BANNER ─────────────────────────────────────────────
    st.markdown(f"""
    <div class='insight-banner'>
      <div class='insight-label'>Key Return Insight — {product_name}</div>
      <div class='insight-text'>{top_insight}</div>
    </div>""", unsafe_allow_html=True)

    # ── 2. METRIC CARDS ───────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        src_html = "".join(
            f"<div><span class='source-badge badge-{k}'>{k.replace('_',' ').title()} {v}</span></div>"
            for k, v in sources.items()
        )
        st.markdown(f"<div class='metric-card'>{src_html}<div class='metric-label'>Data Sources</div></div>",
                    unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{sentiment['total']}</div>"
                    f"<div class='metric-label'>Reviews Analyzed</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#ef4444'>{low_star_n}</div>"
                    f"<div class='metric-label'>1–3 Star Reviews</div></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#ef4444'>"
                    f"{sentiment['negative_pct']}%</div>"
                    f"<div class='metric-label'>Negative Sentiment</div></div>", unsafe_allow_html=True)
    with m5:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:{health['color']}'>"
                    f"{health['score']}</div><div class='metric-label'>Health Score / 100 — "
                    f"{health['status']}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3. CHARTS ─────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='sec-title'>Sentiment Breakdown</div>", unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Positive", "Neutral", "Negative"],
            values=[sentiment["positive"], sentiment["neutral"], sentiment["negative"]],
            hole=0.60,
            marker=dict(colors=["#22c55e","#6366f1","#ef4444"], line=dict(color="#0f0f15", width=3)),
            textinfo="percent+label", textfont=dict(color="white", size=12),
        ))
        fig.update_layout(**_dark(h=300, showlegend=False),
            annotations=[dict(text=f"<b>{sentiment['total']}</b><br>reviews",
                              x=0.5, y=0.5, font_size=14, showarrow=False, font_color="white")])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<div class='sec-title'>Complaint Categories (1–3 Star Reviews)</div>",
                    unsafe_allow_html=True)
        if themes:
            top6 = themes[:7]
            names  = [t["theme"] for t in top6]
            pcts   = [t["pct"]   for t in top6]
            colors = [THEME_COLORS.get(n, "#6b7280") for n in names]
            fig2 = go.Figure()
            for i, (name, pct) in enumerate(zip(names, pcts)):
                fig2.add_trace(go.Bar(x=[pct], y=[name], orientation="h",
                    marker_color=colors[i], text=f" {pct}%", textposition="outside",
                    textfont=dict(color="white", size=12), name=name, showlegend=False, width=0.55))
            fig2.update_layout(**_dark(h=max(280, len(top6)*50), margin=dict(t=10,b=20,l=0,r=70)),
                xaxis=dict(ticksuffix="%", gridcolor="#2a2a3a", color="#94a3b8",
                           range=[0, max(pcts)*1.35] if pcts else [0,100]),
                yaxis=dict(tickfont=dict(color="#e2e8f0", size=11), gridcolor="#2a2a3a", autorange="reversed"),
                barmode="group")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No complaint themes detected.")

    # Pie chart — complaint share
    if themes and len(themes) >= 2:
        st.markdown("<div class='sec-title'>Complaint Distribution</div>", unsafe_allow_html=True)
        fig3 = go.Figure(go.Pie(
            labels=[t["theme"] for t in themes],
            values=[t["count"] for t in themes],
            marker=dict(colors=[THEME_COLORS.get(t["theme"],"#6b7280") for t in themes],
                        line=dict(color="#0f0f15", width=2)),
            textinfo="percent+label", textfont=dict(color="white", size=11),
        ))
        fig3.update_layout(**_dark(h=300, showlegend=False))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── 4. TOP KEYWORDS ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>Top Negative Keywords (from 1–3 star reviews)</div>",
                unsafe_allow_html=True)
    if keywords:
        kc = ["#ff4d6d","#ff8c42","#f59e0b","#ffd447","#a78bfa","#4d9fff","#4dffa6","#06b6d4"]
        kw_html = " ".join([
            f"<span style='background:{kc[i%len(kc)]}22;border:1px solid {kc[i%len(kc)]};"
            f"color:{kc[i%len(kc)]} !important;padding:5px 14px;border-radius:20px;"
            f"font-size:.82rem;margin:3px;display:inline-block;font-weight:600'>{k['keyword']}</span>"
            for i, k in enumerate(keywords[:20])
        ])
        st.markdown(kw_html, unsafe_allow_html=True)
    else:
        st.info("Not enough reviews to extract keywords.")

    # ── 5. LLM CLUSTER CARDS ──────────────────────────────────────────────
    if clusters:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='sec-title'>LLM Cluster Analysis — Semantic Groups</div>",
                    unsafe_allow_html=True)
        st.caption("Reviews grouped by meaning using sentence-transformer embeddings, then mapped to complaint themes.")
        cl_cols = st.columns(min(3, len(clusters)))
        for i, cl in enumerate(clusters[:6]):
            with cl_cols[i % len(cl_cols)]:
                tc = THEME_COLORS.get(cl["theme"], "#6b7280")
                kw_tags = " ".join(f"<span class='kw-tag'>{kw}</span>" for kw in cl["keywords"])
                st.markdown(f"""
                <div class='cluster-card'>
                  <div style='font-size:.9rem;font-weight:700;color:{tc} !important;margin-bottom:4px'>{cl['theme']}</div>
                  <div style='font-size:.75rem;color:#6b7280 !important'>{cl['size']} reviews · {cl['pct']}% of complaints</div>
                  <div style='margin-top:7px'>{kw_tags}</div>
                  <div style='font-size:.82rem;color:#94a3b8 !important;font-style:italic;margin-top:8px'>"{cl['sample']}"</div>
                </div>""", unsafe_allow_html=True)

    # ── 6. LISTING COMPARISON TABLE ───────────────────────────────────────
    if themes:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='sec-title'>Review Complaints vs Product Listing — What to Fix</div>",
                    unsafe_allow_html=True)
        st.caption("Map each complaint directly to a fix in your product listing or operations.")

        listing_fixes = {
            "Sizing / Fit Issue":   "Add size chart with exact cm/inch measurements + guide image",
            "Product Quality":      "Add quality guarantee, close-up photos, material specs to listing",
            "Misleading Listing":   "Reshoot in natural light; audit description vs actual product",
            "Packaging Issue":      "Upgrade to double-walled box; show packaging in listing photos",
            "Delivery / Logistics": "Switch courier; show realistic delivery estimate in listing",
            "Customer Service":     "Add WhatsApp support link + clear return policy to listing",
            "Price / Value":        "Add value comparison or bundle offer to listing",
            "Missing Parts":        "List all included items in description with labeled photos",
        }

        rows = [(t["theme"], f"{t['pct']}%", t["count"],
                 listing_fixes.get(t["theme"], "Review listing accuracy")) for t in themes[:8]]

        fig_t = go.Figure(go.Table(
            header=dict(
                values=["<b>Complaint Theme</b>","<b>% Reviews</b>","<b>Count</b>","<b>Fix in Listing</b>"],
                fill_color="#1a1a24", font=dict(color="white", size=12),
                align="left", line_color="#2a2a3a", height=36),
            cells=dict(
                values=[[r[0] for r in rows],[r[1] for r in rows],
                        [r[2] for r in rows],[r[3] for r in rows]],
                fill_color=["#111118","#111118","#111118","#111118"],
                font=dict(color=["#e2e8f0","#ef4444","#94a3b8","#a5b4fc"], size=12),
                align="left", line_color="#2a2a3a", height=34),
        ))
        fig_t.update_layout(**_dark(h=max(240, len(rows)*42+50), margin=dict(t=0,b=0,l=0,r=0)))
        st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})

    # ── 7. SELLER ACTION PLAN ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>Seller Action Plan</div>", unsafe_allow_html=True)

    if recs:
        for rec in recs:
            p = rec["priority"]
            pb_cls = f"pb-{p.lower()}"
            actions_html = "".join(
                f"<div class='rec-action'>→ {a}</div>" for a in rec["actions"])
            ex_html = ""
            if rec.get("examples"):
                ex_html = (f"<div style='margin-top:9px;font-size:.79rem;color:#6b7280 !important;"
                           f"padding:7px 11px;background:rgba(255,255,255,.03);border-radius:6px'>"
                           f"Customer said: \"{rec['examples'][0][:140]}...\"</div>")
            st.markdown(f"""
            <div class='rec-card rec-card-{p}'>
              <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
                <b style='color:#fff !important;font-size:1rem'>{rec['theme']}</b>
                <span class='{pb_cls}'>{rec['priority_label']}</span>
              </div>
              <div class='rec-insight'>{rec['insight']}</div>
              {actions_html}
              {ex_html}
            </div>""", unsafe_allow_html=True)
    else:
        st.success("No major complaints detected. Product looks healthy!")

    # ── 8. PROBLEM REVIEWS ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    problem = sorted(
        [r for r in reviews if r.get("sentiment") in ("NEGATIVE","NEUTRAL")],
        key=lambda x: 0 if x.get("sentiment") == "NEGATIVE" else 1
    )
    if problem:
        st.markdown(f"<div class='sec-title'>Problem Reviews — {len(problem)} shown "
                    f"(positive hidden)</div>", unsafe_allow_html=True)
        for r in problem[:30]:
            s = r.get("sentiment","NEUTRAL")
            rt = r.get("rating",0)
            src = r.get("source","")
            txt = r.get("text","")[:280]
            cc = "rev-card-neg" if s=="NEGATIVE" else "rev-card-neu"
            bc = "rb-neg"       if s=="NEGATIVE" else "rb-neu"
            star = f"<span class='rev-badge rb-star'>★ {rt}</span>" if rt else ""
            st.markdown(f"""
            <div class='rev-card {cc}'>
              <div class='rev-text'>{txt}</div>
              <div><span class='rev-badge {bc}'>{s}</span>{star}
                   <span class='rev-badge rb-src'>{src}</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.success("No negative or neutral reviews found!")


# ── TRIGGER ───────────────────────────────────────────────────────────────────
if analyze_clicked:
    if not user_input.strip():
        st.warning("Please enter a product URL or product name.")
    else:
        with st.spinner("Collecting reviews from all sources..."):
            result = collect_all(
                input_text=user_input.strip(),
                max_pages=max_pages,
                use_reddit=use_reddit,
                use_google=use_google,
                youtube_api_key=youtube_key,
                twitter_bearer_token=twitter_token,
            )
        if result["total"] == 0:
            st.error("Could not collect any reviews. Try typing the product name directly "
                     "(e.g. 'boAt Airdopes 141') or enable Reddit in the sidebar.")
        else:
            st.success(
                f"Collected **{result['total']} reviews** for **{result['product_name']}** — "
                + ", ".join(f"{k} ({v})" for k, v in result["sources"].items())
            )
            run_analysis(result["reviews"], result["product_name"], result["sources"])
else:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""**Amazon URL**
```
https://www.amazon.in/dp/B09...
https://amzn.in/d/...
```""")
    with c2:
        st.markdown("""**Flipkart URL**
```
https://www.flipkart.com/...
```""")
    with c3:
        st.markdown("""**Or type product name**
```
boAt Airdopes 141
Samsung Galaxy Buds
```""")
    st.markdown("""
---
**What this tool does:**
1. Scrapes Amazon / Flipkart + Reddit + YouTube + Google Shopping
2. Focuses on **1–3 star reviews** (where return signals hide)
3. Uses **LLM sentence-transformer clustering** to group complaints by meaning
4. Maps to 5 themes: Sizing · Quality · Packaging · Delivery · Misleading Listing
5. Generates insights: *"38% of negative reviews say the color doesn't match the listing photo."*
6. Gives a **prioritized seller fix plan** — HIGH / MEDIUM / LOW per category
""")
