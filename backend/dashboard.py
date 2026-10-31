
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="AI Document Assistant | Evaluation",
    page_icon="◆",
    layout="wide"
)

# ---------- STYLE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0B1020;
    color: #E8ECF5;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background: #11182A;
    border-right: 1px solid #27334B;
}

h1, h2, h3 {
    color: #F4F6FC !important;
}

p, label {
    color: #A7B1C7;
}

.metric-card {
    background: linear-gradient(145deg, #17233B, #111A2D);
    border: 1px solid #2B3B58;
    border-radius: 14px;
    padding: 22px;
    min-height: 145px;
}

.metric-label {
    color: #9BAAC4;
    font-size: 13px;
    font-weight: 600;
}

.metric-value {
    color: #F4F6FC;
    font-size: 34px;
    font-weight: 800;
    margin-top: 12px;
}

.metric-description {
    color: #8493AE;
    font-size: 12px;
    margin-top: 8px;
}

.section-card {
    background: #111A2D;
    border: 1px solid #273650;
    border-radius: 14px;
    padding: 22px;
}

.status-good {
    color: #48D6A0;
    font-weight: 700;
}

.status-bad {
    color: #FF727C;
    font-weight: 700;
}

.subtitle {
    color: #8493AE;
    font-size: 14px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #273650;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ---------- DATA ----------
FILE_PATH = Path("evaluation_results.csv")

st.sidebar.markdown("## AI OBSERVABILITY")
st.sidebar.caption("Document Assistant")

if not FILE_PATH.exists():
    st.error("Evaluation file not found. Run run_evaluation.py first.")
    st.stop()

df = pd.read_csv(FILE_PATH)

if df.empty:
    st.warning("No evaluation data available.")
    st.stop()

required_columns = [
    "question",
    "faithfulness",
    "answer_relevance",
    "hallucination_score",
    "latency",
    "source_found"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"Missing columns in CSV: {missing}")
    st.stop()

for col in ["faithfulness", "answer_relevance",
            "hallucination_score", "latency"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["source_found"] = (
    df["source_found"].astype(str).str.lower() == "true"
)

df = df.dropna(subset=["latency"])

# ---------- SIDEBAR ----------
st.sidebar.divider()
st.sidebar.markdown("### Evaluation overview")
st.sidebar.metric("Total test cases", len(df))
st.sidebar.metric(
    "Sources retrieved",
    f"{df['source_found'].sum()} / {len(df)}"
)

st.sidebar.divider()
st.sidebar.caption("RAG Evaluation System")
st.sidebar.caption("LLM-as-a-Judge · Groq")


# ---------- HEADER ----------
st.markdown("# AI Document Assistant")
st.markdown(
    '<p class="subtitle">RAG Quality & Performance Monitoring</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<span class="status-good">● Evaluation data loaded</span>'
    ' &nbsp;&nbsp; <span class="subtitle">Latest evaluation results</span>',
    unsafe_allow_html=True
)

st.divider()

# ---------- METRICS ----------
st.markdown("## Performance overview")

faithfulness = df["faithfulness"].mean()
relevance = df["answer_relevance"].mean()
hallucination_free = df["hallucination_score"].mean()
retrieval = df["source_found"].mean()
latency = df["latency"].mean()

metrics = [
    ("Faithfulness", faithfulness, "Grounded in document context"),
    ("Answer relevance", relevance, "Answers the user's question"),
    ("Hallucination-free", hallucination_free, "No unsupported claims detected"),
    ("Retrieval accuracy", retrieval, "Expected source successfully retrieved")
]

cols = st.columns(4)

for col, (name, value, description) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{name}</div>
            <div class="metric-value">{value:.0%}</div>
            <div class="metric-description">{description}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

lat_col1, lat_col2 = st.columns([1, 3])

with lat_col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Average response latency</div>
        <div class="metric-value">{latency:.2f}s</div>
        <div class="metric-description">Average RAG generation time</div>
    </div>
    """, unsafe_allow_html=True)

with lat_col2:
    st.markdown("""
    <div class="section-card">
        <div class="metric-label">WHAT THESE METRICS MEAN</div>
        <p>
        These indicators evaluate whether the RAG system retrieves
        relevant information and generates accurate answers grounded
        in the uploaded documents.
        </p>
        <p>
        Quality scores are produced by an LLM evaluator.
        They should be interpreted as estimates, not absolute guarantees.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.divider()

# ---------- QUALITY CHART ----------
st.markdown("## Quality analysis")

quality_names = [
    "Faithfulness",
    "Answer relevance",
    "Hallucination-free",
    "Retrieval accuracy"
]

quality_values = [
    faithfulness,
    relevance,
    hallucination_free,
    retrieval
]

fig_quality = go.Figure(
    go.Bar(
        x=quality_values,
        y=quality_names,
        orientation="h",
        text=[f"{v:.0%}" for v in quality_values],
        textposition="outside",
        marker=dict(color="#668BFF")
    )
)

fig_quality.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111A2D",
    plot_bgcolor="#111A2D",
    height=330,
    margin=dict(l=10, r=45, t=20, b=20),
    xaxis=dict(range=[0, 1.15], tickformat=".0%"),
    yaxis=dict(autorange="reversed"),
    showlegend=False
)

st.plotly_chart(fig_quality, use_container_width=True)

st.divider()

# ---------- LATENCY ----------
st.markdown("## Response performance")

latency_df = df.copy()
latency_df["test_number"] = [
    f"Test {i+1}" for i in range(len(latency_df))
]

fig_latency = go.Figure(
    go.Bar(
        x=latency_df["test_number"],
        y=latency_df["latency"],
        text=[f"{v:.2f}s" for v in latency_df["latency"]],
        textposition="outside",
        marker=dict(color="#20BFA9")
    )
)

fig_latency.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111A2D",
    plot_bgcolor="#111A2D",
    height=320,
    margin=dict(l=10, r=20, t=20, b=20),
    yaxis_title="Seconds",
    xaxis_title="Evaluation case"
)

st.plotly_chart(fig_latency, use_container_width=True)

st.divider()

# ---------- TEST TABLE ----------
st.markdown("## Test case results")

table = df[[
    "question",
    "faithfulness",
    "answer_relevance",
    "hallucination_score",
    "source_found",
    "latency"
]].copy()

table.columns = [
    "Question",
    "Faithfulness",
    "Relevance",
    "Hallucination-free",
    "Source found",
    "Latency (s)"
]

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Faithfulness": st.column_config.ProgressColumn(
            min_value=0, max_value=1, format="%.0%"
        ),
        "Relevance": st.column_config.ProgressColumn(
            min_value=0, max_value=1, format="%.0%"
        ),
        "Hallucination-free": st.column_config.ProgressColumn(
            min_value=0, max_value=1, format="%.0%"
        ),
        "Source found": st.column_config.CheckboxColumn()
    }
)

# ---------- ANSWER INSPECTION ----------
st.markdown("## Answer inspection")

for i, row in df.iterrows():
    with st.expander(f"Test {i+1} — {row['question']}"):

        st.markdown("**Generated answer**")
        st.write(row.get("answer", "Not available"))

        st.markdown("**Evaluator reasoning**")
        st.write(row.get("reasoning", "Not available"))

        score = row["hallucination_score"]

        if score >= 1:
            st.markdown(
                '<span class="status-good">No hallucination detected</span>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span class="status-bad">Potential hallucination detected</span>',
                unsafe_allow_html=True
            )

st.divider()

st.caption(
    "AI Document Assistant | RAG Evaluation Dashboard | "
    "Metrics based on the latest evaluation run."
)
