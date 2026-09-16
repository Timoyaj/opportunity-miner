"""Streamlit CRM and Opportunity Intelligence Dashboard."""

import streamlit as st
from datetime import datetime
import json
from pathlib import Path
import pandas as pd

from opportunity_miner.database.session import get_db, init_db
from opportunity_miner.database.models import Opportunity, ProblemCluster, ExtractedProblem, RawSignal, UserFeedback
from opportunity_miner.core.vector_store import VectorStore
from opportunity_miner.adapters import ADAPTERS_MAP, get_adapter

st.set_page_config(
    page_title="OpportunityMiner AI CRM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ---------------------------------------------------------------------------
# DESIGN SYSTEM
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f6f8fb;
    --surface: #ffffff;
    --border: #e5e9f0;
    --text: #0f172a;
    --muted: #64748b;
    --primary: #2563eb;
    --primary-dark: #1e40af;
}

/* Global */
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif !important;
}
[data-testid="stAppViewContainer"] { background: var(--bg); }
.block-container { padding-top: 2.2rem; max-width: 1400px; }

h1 { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; color: var(--text); }
h2 { font-size: 1.2rem; font-weight: 700; letter-spacing: -0.01em; }
h3 { font-size: 1.02rem; font-weight: 600; }

/* Hide default chrome clutter */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220 0%, #101b30 100%);
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: #f8fafc !important; font-weight: 700;
}
.sidebar-logo {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    border-radius: 14px; padding: 18px; margin-bottom: 12px; color: #fff !important;
}
.sidebar-logo h2 { color: #ffffff !important; margin: 0 0 4px 0; font-size: 1.15rem; }
.sidebar-logo p { color: #dbeafe !important; margin: 0; font-size: 0.78rem; }
[data-testid="stSidebar"] hr { border-color: #1e293b; }

/* Radio nav pill styling */
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent; border-radius: 10px; padding: 4px 8px;
    transition: background 0.15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.06); }

/* KPI cards */
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.03);
    height: 100%;
}
.kpi-card .kpi-icon {
    font-size: 1.3rem; width: 40px; height: 40px; display: inline-flex;
    align-items: center; justify-content: center; border-radius: 10px;
    background: #eff6ff; margin-bottom: 10px;
}
.kpi-card .kpi-value { font-size: 1.9rem; font-weight: 800; color: var(--text); line-height: 1.1; }
.kpi-card .kpi-label { font-size: 0.78rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--muted); margin-top: 4px; }
.kpi-card .kpi-sub { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

/* Generic panel card */
.panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 20px 22px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

/* Pills */
.pill { display: inline-block; padding: 3px 12px; border-radius: 9999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em; }
.pill-high  { background: #dcfce7; color: #166534; }
.pill-med   { background: #fef9c3; color: #854d0e; }
.pill-low   { background: #fee2e2; color: #991b1b; }
.pill-blue  { background: #dbeafe; color: #1d4ed8; }
.pill-purple{ background: #ede9fe; color: #5b21b6; }
.pill-gray  { background: #f1f5f9; color: #475569; }
.pill-green { background: #dcfce7; color: #15803d; }
.pill-red   { background: #fee2e2; color: #b91c1c; }

/* Opportunity list card */
.opp-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px 18px; margin-bottom: 10px;
    display: flex; align-items: center; gap: 16px;
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.opp-card:hover { box-shadow: 0 6px 18px rgba(15,23,42,0.08); }
.opp-score {
    min-width: 64px; height: 64px; border-radius: 12px; display: flex;
    flex-direction: column; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1.35rem; color: #fff;
}
.score-grad-high { background: linear-gradient(135deg, #16a34a, #059669); }
.score-grad-med  { background: linear-gradient(135deg, #d97706, #f59e0b); }
.score-grad-low  { background: linear-gradient(135deg, #9ca3af, #6b7280); }
.opp-score small { font-size: 0.62rem; font-weight: 600; opacity: 0.85; }
.opp-body { flex: 1; }
.opp-title { font-weight: 700; font-size: 0.98rem; color: var(--text); }
.opp-meta { font-size: 0.78rem; color: var(--muted); margin-top: 4px; }

/* Score breakdown bar */
.bd-row { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
.bd-label { width: 150px; font-size: 0.78rem; color: var(--muted); font-weight: 600; }
.bd-track { flex: 1; height: 8px; background: #eef2f7; border-radius: 9999px; overflow: hidden; }
.bd-fill { height: 100%; border-radius: 9999px; background: linear-gradient(90deg, #3b82f6, #2563eb); }
.bd-val { width: 60px; text-align: right; font-size: 0.75rem; font-weight: 700; color: var(--text); }

/* Offer ladder tier cards */
.tier-card { border-radius: 14px; padding: 18px; height: 100%;
    border: 1px solid var(--border); background: var(--surface); }
.tier-1 { border-top: 4px solid #3b82f6; }
.tier-2 { border-top: 4px solid #8b5cf6; }
.tier-3 { border-top: 4px solid #10b981; }
.tier-card h4 { margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 700; }
.tier-card .tier-price { font-size: 1.15rem; font-weight: 800; color: var(--primary); margin: 6px 0; }
.tier-card p { font-size: 0.85rem; color: var(--muted); }

/* Quote blocks (verbatim evidence) */
.quote {
    border-left: 3px solid #3b82f6; background: #f8fafc;
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 8px 0;
    font-style: italic; color: #334155; font-size: 0.88rem;
}

/* Cluster card */
.cluster-card { background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04); }
.cluster-stats { display: flex; gap: 28px; margin-top: 8px; }
.cluster-stat .v { font-weight: 800; font-size: 1.05rem; color: var(--text); }
.cluster-stat .k { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); font-weight: 600; }

/* Section heading with accent bar */
.section-head { display: flex; align-items: center; gap: 10px; margin: 6px 0 14px 0; }
.section-head .bar { width: 4px; height: 20px; border-radius: 4px; background: var(--primary); }
.section-head h2 { margin: 0; }

/* Streamlit expander polish */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important; border-radius: 12px !important;
    background: var(--surface) !important; overflow: hidden;
}

/* Buttons */
.stButton > button {
    border-radius: 10px; font-weight: 600; border: 1px solid var(--border);
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background: var(--primary); border-color: var(--primary); color: #fff;
}
.stButton > button[kind="primary"]:hover { background: var(--primary-dark); }

/* Metrics restyle */
[data-testid="stMetric"] {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-weight: 600 !important; }

/* Dataframe container */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SHARED UI HELPERS
# ---------------------------------------------------------------------------
def score_pill_class(score: float) -> str:
    if score >= 70:
        return "pill-high"
    if score >= 50:
        return "pill-med"
    return "pill-low"


def score_grad_class(score: float) -> str:
    if score >= 70:
        return "score-grad-high"
    if score >= 50:
        return "score-grad-med"
    return "score-grad-low"


STATUS_PILL = {
    "NEW": "pill-blue", "INVESTIGATING": "pill-purple", "VALIDATING": "pill-med",
    "PROTOTYPING": "pill-purple", "PAID_PROJECT": "pill-green", "REJECTED": "pill-red",
    "ARCHIVED": "pill-gray",
}


def render_section(title: str):
    st.markdown(f'<div class="section-head"><div class="bar"></div><h2>{title}</h2></div>',
                unsafe_allow_html=True)


def render_kpi(icon: str, value, label: str, sub: str = ""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


def score_breakdown_bar(bd: dict):
    rows = [
        ("Pain Intensity", bd.get("pain", 0), 25),
        ("Market Frequency", bd.get("frequency", 0), 15),
        ("Willingness to Pay", bd.get("willingness_to_pay", 0), 20),
        ("Market Recurrence", bd.get("market_recurrence", 0), 15),
    ]
    for label, val, max_v in rows:
        pct = int((val / max_v) * 100) if max_v else 0
        st.markdown(f"""
        <div class="bd-row">
            <div class="bd-label">{label}</div>
            <div class="bd-track"><div class="bd-fill" style="width:{min(pct, 100)}%"></div></div>
            <div class="bd-val">{val}/{max_v}</div>
        </div>
        """, unsafe_allow_html=True)


st.sidebar.markdown("""
<div class="sidebar-logo">
    <h2>🎯 OpportunityMiner</h2>
    <p>Evidence-Driven Commercial<br>Opportunity Engine</p>
</div>
""", unsafe_allow_html=True)

view = st.sidebar.radio(
    "Navigation",
    ["📊 Executive Dashboard", "💼 Opportunity CRM", "🔬 Dossier Detail", "🌐 Problem Clusters", "🚫 Negative Blacklist"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("v1.0 · AI Opportunity Intelligence")


def load_kpis():
    with get_db() as db:
        signals_count = db.query(RawSignal).count()
        problems_count = db.query(ExtractedProblem).count()
        clusters_count = db.query(ProblemCluster).count()
        opps_count = db.query(Opportunity).count()
        high_opps_count = db.query(Opportunity).filter(Opportunity.opportunity_score >= 70).count()
        return signals_count, problems_count, clusters_count, opps_count, high_opps_count


# VIEW 1: EXECUTIVE DASHBOARD
if view == "📊 Executive Dashboard":
    st.title("Executive Intelligence Dashboard")
    st.caption("Real-time telemetry across signals, verified problems, and commercial opportunities.")

    sig_c, prob_c, clust_c, opp_c, high_c = load_kpis()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi("📡", sig_c, "Raw Signals", "ingested posts & listings")
    with k2:
        render_kpi("🧩", prob_c, "Problems", "structured extractions")
    with k3:
        render_kpi("🌐", clust_c, "Clusters", "semantic groups")
    with k4:
        render_kpi("💼", opp_c, "Opportunities", "commercialized")
    with k5:
        render_kpi("🔥", high_c, "High Value", "score ≥ 70")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        render_section("Source Coverage & Status")
        status_data = []
        for name in ADAPTERS_MAP:
            try:
                adapter = get_adapter(name)
                is_ok, msg = adapter.health_check()
                status_data.append({
                    "Source": name.capitalize(),
                    "Status": "🟢 ONLINE" if is_ok else "🟡 OFFLINE",
                    "Details": msg
                })
            except Exception as e:
                status_data.append({"Source": name.capitalize(), "Status": "🔴 ERROR", "Details": str(e)})
        st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)

    with col_right:
        render_section("Opportunity Score Distribution")
        with get_db() as db:
            opps = db.query(Opportunity.opportunity_score, Opportunity.category).all()
            if opps:
                df_opps = pd.DataFrame(opps, columns=["Score", "Category"])
                st.bar_chart(df_opps["Category"].value_counts())
            else:
                st.info("No opportunities currently scored in database.")


# VIEW 2: OPPORTUNITY CRM
elif view == "💼 Opportunity CRM":
    st.title("Commercial Opportunity CRM")
    st.caption("Manage and track verified commercial opportunities through the validation lifecycle.")

    with get_db() as db:
        opps = db.query(Opportunity).all()

        if not opps:
            st.info("No opportunities currently in database. Run `opportunity-miner scan` in terminal to populate.")
        else:
            # Filter bar
            c1, c2, c3 = st.columns([1, 1, 1])
            status_filter = c1.selectbox("Filter Status", ["ALL", "NEW", "INVESTIGATING", "VALIDATING", "PAID_PROJECT", "REJECTED"])
            cat_filter = c2.selectbox("Filter Category", ["ALL"] + list(set(o.category for o in opps)))
            min_score = c3.slider("Minimum Opportunity Score", 0.0, 100.0, 50.0)

            filtered = [
                o for o in opps
                if (status_filter == "ALL" or o.status == status_filter)
                and (cat_filter == "ALL" or o.category == cat_filter)
                and o.opportunity_score >= min_score
            ]

            st.markdown(f'<span class="pill pill-blue">{len(filtered)} of {len(opps)} opportunities shown</span>',
                        unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            for opp in sorted(filtered, key=lambda x: x.opportunity_score, reverse=True):
                grad = score_grad_class(opp.opportunity_score)
                st.markdown(f"""
                <div class="opp-card">
                    <div class="opp-score {grad}">{int(opp.opportunity_score)}<small>/ 100</small></div>
                    <div class="opp-body">
                        <div class="opp-title">{opp.title}</div>
                        <div class="opp-meta">
                            <code>{opp.id}</code> · {opp.category} · Evidence L{opp.evidence_level} ·
                            Confidence {int(opp.confidence_score * 100)}%
                        </div>
                    </div>
                    <span class="pill {STATUS_PILL.get(opp.status, 'pill-gray')}">{opp.status.replace('_', ' ')}</span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("⚙️ Manage & Inspect Score Breakdown"):
                    render_section("Score Breakdown")
                    score_breakdown_bar(opp.score_breakdown)

                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    col_stat, col_btn = st.columns([2, 1])
                    statuses = ["NEW", "INVESTIGATING", "VALIDATING", "PROTOTYPING", "PAID_PROJECT", "REJECTED", "ARCHIVED"]
                    new_status = col_stat.selectbox(
                        "Update Pipeline Status",
                        statuses,
                        index=statuses.index(opp.status),
                        key=f"status_{opp.id}"
                    )
                    if col_btn.button("Save Status", key=f"btn_{opp.id}", type="primary", use_container_width=True):
                        opp.status = new_status
                        db.commit()
                        st.success(f"Status updated to {new_status}")
                        st.rerun()


# VIEW 3: DOSSIER DETAIL
elif view == "🔬 Dossier Detail":
    st.title("Opportunity Dossier Detail View")

    with get_db() as db:
        opps = db.query(Opportunity).order_by(Opportunity.opportunity_score.desc()).all()
        if not opps:
            st.info("No opportunities available.")
        else:
            opp_options = {f"[{o.id}] {o.title} ({int(o.opportunity_score)} pts)": o.id for o in opps}
            selected_label = st.selectbox("Select Opportunity to Inspect", list(opp_options.keys()))
            selected_id = opp_options[selected_label]

            opp = db.query(Opportunity).filter(Opportunity.id == selected_id).first()

            if opp:
                pill = STATUS_PILL.get(opp.status, "pill-gray")
                st.markdown(f"""
                <div class="panel">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
                        <div>
                            <h1 style="font-size:1.35rem; margin:0;">{opp.title}</h1>
                            <div style="margin-top:8px; font-size:0.85rem; color:var(--muted);">
                                <code>{opp.id}</code> · {opp.category}
                            </div>
                        </div>
                        <span class="pill {pill}">{opp.status.replace('_', ' ')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    render_kpi("🎯", f"{int(opp.opportunity_score)}/100", "Opportunity Score")
                with m2:
                    render_kpi("📑", f"L{opp.evidence_level}/5", "Evidence Level")
                with m3:
                    render_kpi("🛡️", f"{int(opp.confidence_score * 100)}%", "Confidence")
                with m4:
                    render_kpi("🛠️", f"{int(opp.technical_feasibility)}/15", "Technical Feasibility")

                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                tab_sol, tab_ev, tab_pkg = st.tabs(["🚀 Solution & Architecture", "📄 Verbatim Evidence Vault", "💼 Commercial Packaging & Outreach"])

                with tab_sol:
                    sol = opp.solution_hypothesis
                    render_section("Proposed Technical Workflow")
                    st.write(sol.get("proposed_workflow", "Automated pipeline implementation."))

                    render_section("Recommended Technology Stack")
                    st.code(", ".join(sol.get("technology_stack", ["Python", "pandas"])))

                    mvp = sol.get("mvp_scope", {})
                    render_section("Core MVP Deliverables")
                    for feat in mvp.get("core_features", []):
                        st.markdown(f"- {feat}")

                with tab_ev:
                    render_section("Verbatim Evidence Collected from Sources")
                    if opp.cluster and opp.cluster.problems:
                        for prob in opp.cluster.problems:
                            st.markdown(f"**Extracted Problem ({prob.id}):** {prob.problem_statement}")
                            st.markdown(f"*Root Cause:* {prob.underlying_problem}")
                            st.markdown(f"*Current Workaround:* `{prob.current_workaround}`")

                            quotes = prob.pain_evidence
                            if quotes:
                                st.markdown("**Verbatim Pain Quotes:**")
                                for q in quotes:
                                    st.markdown(f'<div class="quote">"{q}"</div>', unsafe_allow_html=True)

                            if prob.signal:
                                st.markdown(f"🔗 **Original Source:** [{prob.signal.source} URL]({prob.signal.source_url}) (Author: `{prob.signal.author}`)")
                            st.markdown("---")
                    else:
                        st.info("No linked evidence records for this opportunity.")


                with tab_pkg:
                    render_section("3-Stage Commercial Offer Escalation Ladder")
                    pkg = opp.commercial_packaging
                    ladder = pkg.get("offer_ladder", {})

                    t1 = ladder.get("tier_1_foot_in_the_door", {})
                    t2 = ladder.get("tier_2_monthly_retainer", {})
                    t3 = ladder.get("tier_3_productized_saas", {})

                    c1, c2, c3 = st.columns(3)
                    for col, tier_cls, tier_tag, tier in [
                        (c1, "tier-1", "TIER 1 · Foot-in-Door", t1),
                        (c2, "tier-2", "TIER 2 · Retainer", t2),
                        (c3, "tier-3", "TIER 3 · Micro-SaaS", t3),
                    ]:
                        with col:
                            st.markdown(f"""
                            <div class="tier-card {tier_cls}">
                                <span class="pill pill-blue">{tier_tag}</span>
                                <h4 style="margin-top:10px;">{tier.get('name', '—')}</h4>
                                <div class="tier-price">{tier.get('price', '—')}</div>
                                <p>{tier.get('deliverable', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    render_section("Consultative Outreach Message Draft")
                    outreach = pkg.get("outreach_message", "")
                    st.text_area("Direct Message Draft (Ready to copy)", value=outreach, height=180)


# VIEW 4: PROBLEM CLUSTERS
elif view == "🌐 Problem Clusters":
    st.title("Problem Clusters & Semantic Groups")
    with get_db() as db:
        clusters = db.query(ProblemCluster).order_by(ProblemCluster.mention_count.desc()).all()
        if not clusters:
            st.info("No clusters formed yet.")
        else:
            for cl in clusters:
                st.markdown(f"""
                <div class="cluster-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0;">[{cl.id}] {cl.title}</h3>
                        <span class="pill {score_pill_class(min(cl.mention_count * 10, 100))}">{cl.mention_count} mentions</span>
                    </div>
                    <p style="color:var(--muted); margin:8px 0 0 0; font-size:0.88rem;">{cl.description}</p>
                    <div class="cluster-stats">
                        <div class="cluster-stat"><div class="v">{cl.mention_count}</div><div class="k">Mentions</div></div>
                        <div class="cluster-stat"><div class="v">{cl.unique_sources}</div><div class="k">Unique Sources</div></div>
                        <div class="cluster-stat"><div class="v">{cl.trend_velocity:.1f}/wk</div><div class="k">Velocity</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# VIEW 5: NEGATIVE BLACKLIST
elif view == "🚫 Negative Blacklist":
    st.title("User-Rejected Negative Blacklist")
    st.caption("Topics marked as rejected will automatically suppress incoming similar signals at near-zero cost.")

    vstore = VectorStore()
    blacklist_file = Path("data/vectors/negative_blacklist.json")

    if blacklist_file.exists():
        with open(blacklist_file, "r", encoding="utf-8") as f:
            items = json.load(f)
        st.markdown(f'<span class="pill pill-red">{len(items)} active blacklisted vectors</span>',
                    unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        for idx, item in enumerate(items, 1):
            st.markdown(f"""
            <div class="opp-card" style="padding:12px 16px;">
                <span class="pill pill-gray">#{idx}</span>
                <div class="opp-body"><div class="opp-title" style="font-weight:600;">{item.get('reason', 'Unspecified rejection')}</div></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Blacklist is currently empty.")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    render_section("Add Topic to Blacklist")
    topic_to_block = st.text_input("Topic or problem to suppress (e.g. 'dropshipping crypto tools')")
    if st.button("Add to Blacklist", type="primary"):
        if topic_to_block:
            vec = vstore.embed_text(topic_to_block)
            vstore.save_to_blacklist(vec, reason=topic_to_block)
            st.success(f"Topic '{topic_to_block}' added to negative vector blacklist.")
            st.rerun()
