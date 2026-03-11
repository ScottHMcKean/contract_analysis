import csv
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Contract Analysis Pipeline",
    page_icon="<>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers: file-based
# ---------------------------------------------------------------------------

def read_prompt(name: str) -> str:
    path = PROJECT_ROOT / "prompts" / f"{name}.md"
    if path.exists():
        return path.read_text()
    return f"(prompt file not found: {path})"


def load_metadata_csv() -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    with open(PROJECT_ROOT / "metadata.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.setdefault(row["type"], []).append(row)
    return rows


METADATA = load_metadata_csv()

# ---------------------------------------------------------------------------
# Helpers: Databricks SQL connection
# ---------------------------------------------------------------------------

@st.cache_resource
def get_connection():
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
    if not warehouse_id:
        return None
    try:
        from databricks.sdk.core import Config
        from databricks import sql as dbsql
        cfg = Config()
        return dbsql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            credentials_provider=lambda: cfg.authenticate,
        )
    except Exception:
        return None


def run_query(sql: str) -> pd.DataFrame | None:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(data, columns=cols)
    except Exception:
        return None


def table_count(fqn: str) -> int | None:
    df = run_query(f"SELECT COUNT(*) AS cnt FROM {fqn}")
    if df is not None and len(df) > 0:
        return int(df.iloc[0]["cnt"])
    return None


def table_preview(fqn: str, limit: int = 5) -> pd.DataFrame | None:
    return run_query(f"SELECT * FROM {fqn} LIMIT {limit}")


# ---------------------------------------------------------------------------
# Sidebar navigation + config
# ---------------------------------------------------------------------------

PAGES = [
    "Pipeline Overview",
    "1 -- Parse",
    "2 -- Extract",
    "3 -- Assemble",
    "4 -- Classify",
    "5 -- Metadata",
]

st.sidebar.title("Contract Analysis")
st.sidebar.caption("Pipeline Explorer")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

st.sidebar.divider()
catalog = st.sidebar.text_input("Catalog", value="shm")
schema = st.sidebar.text_input("Schema", value="contract")

def fqn(table: str) -> str:
    return f"{catalog}.{schema}.{table}"

connected = get_connection() is not None
st.sidebar.divider()
st.sidebar.markdown(
    f"**SQL connection:** {'Connected' if connected else 'Not connected'}\n\n"
    "**Config**\n"
    "- LLM: `databricks-claude-sonnet-4-5`\n"
    "- Embeddings: `databricks-gte-large-en`\n"
    "- VS Endpoint: `contract_vs`"
)


# ---------------------------------------------------------------------------
# Helper: table display with count + preview
# ---------------------------------------------------------------------------

def show_table(name: str, columns: list[tuple[str, str]], description: str = ""):
    full_name = fqn(name)
    count = table_count(full_name)
    count_str = f"{count:,}" if count is not None else "--"
    label = f"`{name}` -- {count_str} rows -- {description}"

    with st.expander(label, expanded=False):
        col_header = "| Column | Description |\n|---|---|\n"
        col_body = "\n".join(f"| `{c}` | {d} |" for c, d in columns)
        st.markdown(col_header + col_body)

        if connected:
            preview = table_preview(full_name)
            if preview is not None and len(preview) > 0:
                st.caption("Preview (5 rows)")
                st.dataframe(preview, use_container_width=True, hide_index=True)
            elif preview is not None:
                st.caption("Table is empty")
            else:
                st.caption("Could not query table")


# ---------------------------------------------------------------------------
# Page: Pipeline Overview
# ---------------------------------------------------------------------------

def page_overview():
    st.title("Contract Analysis Pipeline")
    st.markdown(
        "Analyze contracts using generative AI on Databricks. "
        "The pipeline parses contract documents, extracts key information, "
        "classifies them (master agreement / amendment / SOW / termination), "
        "and pulls detailed metadata for contract management systems."
    )

    st.subheader("Document Flow")

    counts = {}
    if connected:
        for t in ["bytes", "parsed", "flat", "references", "doc_info",
                   "assembled", "classified",
                   "metadata_master_agreement", "metadata_amendment",
                   "metadata_scope_of_work", "metadata_termination"]:
            counts[t] = table_count(fqn(t))

    c_bytes = counts.get("bytes") or 50000
    c_flat = counts.get("flat") or 44500
    c_failures = max(c_bytes - c_flat, 0) or 5500
    c_assembled = counts.get("assembled") or 3500
    c_classified = counts.get("classified") or 3500
    c_masters = counts.get("metadata_master_agreement") or 1800
    c_amendments = counts.get("metadata_amendment") or 1100
    c_sow = counts.get("metadata_scope_of_work") or 400
    c_term = counts.get("metadata_termination") or 200

    def fmt(n):
        return f"{n:,}"

    labels = [
        f"Volume (PDFs)\n{fmt(c_bytes)} files",
        "01 Parse\nAI_PARSE_DOCUMENT",
        f"Parse failures\n{fmt(c_failures)} files",
        "02 Extract\nReferences + Doc Info",
        "03 Assemble\nVector Search + Context",
        "04 Classify",
        f"Master Agreements\n{fmt(c_masters)}",
        f"Amendments\n{fmt(c_amendments)}",
        f"Scope of Work\n{fmt(c_sow)}",
        f"Terminations\n{fmt(c_term)}",
        "05 Metadata\nField Extraction",
    ]

    node_colors = [
        "#4e79a7", "#59a14f", "#aaa", "#f28e2b", "#e15759",
        "#76b7b2", "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1",
    ]

    source = [0,  0,  1,  3,  4,  5,  5,  5,  5,  6,  7,  8,  9]
    target = [1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 10, 10, 10]
    value  = [c_flat, c_failures, c_flat, c_flat, c_classified,
              c_masters, c_amendments, c_sow, c_term,
              c_masters, c_amendments, c_sow, c_term]

    link_colors = [
        "rgba(89,161,79,0.3)", "rgba(170,170,170,0.3)",
        "rgba(242,142,43,0.3)", "rgba(225,87,89,0.3)",
        "rgba(118,183,178,0.3)",
        "rgba(78,121,167,0.3)", "rgba(242,142,43,0.3)",
        "rgba(89,161,79,0.3)", "rgba(225,87,89,0.3)",
        "rgba(176,122,161,0.3)", "rgba(176,122,161,0.3)",
        "rgba(176,122,161,0.3)", "rgba(176,122,161,0.3)",
    ]

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=30, thickness=30,
            line=dict(color="#333", width=0.5),
            label=labels, color=node_colors,
        ),
        link=dict(source=source, target=target, value=value, color=link_colors),
    )])

    fig.update_layout(
        font=dict(size=14, family="Inter, sans-serif"),
        height=500,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Table Counts")

    if connected:
        table_names = ["bytes", "parsed", "flat", "references", "doc_info",
                       "assembled", "classified",
                       "metadata_master_agreement", "metadata_amendment",
                       "metadata_scope_of_work", "metadata_termination"]
        cols_per_row = 4
        for i in range(0, len(table_names), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, t in enumerate(table_names[i:i + cols_per_row]):
                c = counts.get(t)
                cols[j].metric(t, f"{c:,}" if c is not None else "--")
    else:
        st.info("Connect to a SQL warehouse to see live table counts.")


# ---------------------------------------------------------------------------
# Page: 1 -- Parse
# ---------------------------------------------------------------------------

def page_parse():
    st.title("Stage 1: Parse")
    st.markdown(
        "Downloads contract PDFs from Cook County open data, "
        "reads them into a Delta `bytes` table, parses with `AI_PARSE_DOCUMENT`, "
        "and flattens into a `flat` table with full text, preamble (first N words), "
        "and truncated text (first M words)."
    )

    st.subheader("Configuration")
    cols = st.columns(3)
    cols[0].metric("batch_size", "100")
    cols[1].metric("words_preamble", "100")
    cols[2].metric("words_truncated", "5,000")

    st.subheader("Tables")

    show_table("bytes", [
        ("path", "Full volume path to the file"),
        ("vendor_name", "Vendor name extracted from folder structure"),
        ("file_name", "Original file name"),
        ("content", "Raw binary file content"),
        ("length", "File size in bytes"),
        ("modificationTime", "Last modification timestamp"),
        ("vendor_folder_paths", "Array of all file paths in the vendor folder"),
    ], "Raw file content read from the volume")

    show_table("parsed", [
        ("path", "Full volume path"),
        ("parsed", "Structured output from AI_PARSE_DOCUMENT"),
    ], "AI-parsed document output")

    show_table("flat", [
        ("path", "Full volume path"),
        ("vendor_name", "Vendor name"),
        ("file_name", "Original file name"),
        ("text", "Full extracted text"),
        ("preamble", "First ~100 words of text"),
        ("truncated", "First ~5000 words of text"),
        ("vendor_folder_paths", "Array of all file paths in the vendor folder"),
    ], "Flattened text ready for downstream processing")

    st.subheader("Pipeline Steps")
    st.markdown(
        "1. **Download** PDFs from Cook County open data, filter to Environmental Services\n"
        "2. **Read** files into `bytes` via `READ_FILES` from Unity Catalog volume\n"
        "3. **Parse** with `AI_PARSE_DOCUMENT` (handles PDFs, images, Office files)\n"
        "4. **Flatten** parsed output into `flat` table (text, preamble, truncated)"
    )


# ---------------------------------------------------------------------------
# Page: 2 -- Extract
# ---------------------------------------------------------------------------

def page_extract():
    st.title("Stage 2: Extract")
    st.markdown(
        "Uses an LLM to extract two things from each contract: "
        "(1) referenced agreements and documents, and "
        "(2) key document info (agreement name, type, dates, master/amendment status)."
    )

    st.subheader("Configuration")
    cols = st.columns(2)
    cols[0].metric("batch_size", "100")
    cols[1].metric("max_input_char", "400,000")

    st.subheader("Tables")

    show_table("references", [
        ("path", "Full volume path"),
        ("agreements", "Array of referenced agreement identifiers"),
        ("references", "Array of {section, document} objects for referenced docs"),
    ], "Extracted agreement references and attachments")

    show_table("doc_info", [
        ("path", "Full volume path"),
        ("agreement_name", "Name of the agreement"),
        ("agreement_type", "Type code (MSA, NDA, CSA, SOW, etc.)"),
        ("document_type", "AGREEMENT / AMENDMENT / SCOPE_OF_WORK / TERMINATION / Other"),
        ("effective_date", "Start date of the contract"),
        ("expiry_date", "End date of the contract"),
        ("is_master_agreement", "Boolean -- is this a master agreement"),
        ("related_master_agreement_name", "If amendment, name of the master it modifies"),
        ("amendment_expiry_date", "If amendment, the new expiry date for the master"),
    ], "Key document info extracted by LLM")

    st.subheader("Prompts")

    tab1, tab2 = st.tabs(["references.md", "doc_info.md"])
    with tab1:
        st.markdown(read_prompt("references"))
    with tab2:
        st.markdown(read_prompt("doc_info"))


# ---------------------------------------------------------------------------
# Page: 3 -- Assemble
# ---------------------------------------------------------------------------

def page_assemble():
    st.title("Stage 3: Assemble")
    st.markdown(
        "Creates a `sections` table from parsed documents, sets up Databricks Vector Search indexes, "
        "then assembles a comprehensive context table per contract. Each row includes the "
        "document's own info plus folder-level related documents and semantically similar "
        "documents from vector search."
    )

    st.subheader("Configuration")
    cols = st.columns(3)
    cols[0].metric("VS Endpoint", "contract_vs")
    cols[1].metric("Embedding Model", "databricks-gte-large-en")
    cols[2].metric("vs_char_limit", "8,000")

    st.subheader("Tables")

    show_table("assembled", [
        ("path", "Full volume path"),
        ("vendor_name", "Vendor name"),
        ("file_name", "Original file name"),
        ("preamble", "First ~100 words"),
        ("doc_info", "Own document info (from extract stage)"),
        ("folder_docs", "Doc info for all documents in the same vendor folder"),
        ("vector_search_docs", "Doc info for semantically similar documents"),
    ], "Combined context per contract for classification")

    st.subheader("Vector Search Indexes")

    for idx, desc in [
        ("flat_index", "Full text embeddings for semantic similarity search"),
        ("doc_info_index", "Document info embeddings for finding related contracts"),
    ]:
        st.markdown(f"- **`{idx}`** -- {desc}")

    st.subheader("Assembly Logic")
    st.markdown(
        "For each contract, the assembled context includes:\n"
        "1. **Own info** -- preamble and doc_info for the document itself\n"
        "2. **Folder docs** -- doc_info and preambles from all documents in the same vendor folder\n"
        "3. **Vector search** -- doc_info from semantically similar documents across the corpus\n\n"
        "This rich context enables the classifier to understand relationships between "
        "master agreements, amendments, and other related documents."
    )


# ---------------------------------------------------------------------------
# Page: 4 -- Classify
# ---------------------------------------------------------------------------

def page_classify():
    st.title("Stage 4: Classify")
    st.markdown(
        "Classifies each document: is it a master agreement, does it have amendments, "
        "what are the initial and final expiry dates. Uses the assembled context from step 3."
    )

    st.subheader("Configuration")
    cols = st.columns(3)
    cols[0].metric("LLM", "claude-sonnet-4-5")
    cols[1].metric("batch_size", "100")
    cols[2].metric("max_input_char", "400,000")

    st.subheader("Tables")

    show_table("classified", [
        ("path", "Full volume path"),
        ("is_master_agreement", "Boolean classification"),
        ("has_amendments", "Whether amendments exist for this master"),
        ("initial_master_agreement_expiry_date", "Original expiry date (YYYYMMDD)"),
        ("final_expiry_date", "Final expiry considering all amendments (YYYYMMDD)"),
        ("final_expiry_date_rationale", "LLM explanation for the final date"),
        ("final_expiry_date_source_path", "Path to the document that sets the final date"),
        ("amendments", "Array of amendment objects with paths and date changes"),
        ("rationale", "Overall classification rationale"),
        ("confidence", "Confidence score 1-5"),
    ], "Master agreement classification with amendment tracking")

    st.subheader("Pipeline Steps")
    st.markdown(
        "1. **Classify** -- LLM determines master agreement status, amendments, expiry dates\n"
        "2. **Duplicate resolution** -- resolves cases where an amendment is linked to multiple masters\n"
        "3. **Re-classify** -- affected masters are re-classified after resolution"
    )

    st.subheader("Prompts")

    tab1, tab2 = st.tabs(["classify.md", "duplicate_amendment_resolution.md"])
    with tab1:
        st.markdown(read_prompt("classify"))
    with tab2:
        st.markdown(read_prompt("duplicate_amendment_resolution"))

    st.subheader("Output Schema")
    st.json({
        "is_master_agreement": "boolean",
        "has_amendments": "boolean",
        "initial_master_agreement_expiry_date": "YYYYMMDD",
        "final_expiry_date": "YYYYMMDD",
        "final_expiry_date_rationale": "string",
        "final_expiry_date_source_path": "string",
        "amendments": [
            {
                "amendment_path": "string",
                "changes_master_agreement_expiry": "boolean",
                "new_master_agreement_expiry": "YYYYMMDD",
                "agreement_document_type": "string",
            }
        ],
        "rationale": "string",
        "confidence": "1-5",
    })


# ---------------------------------------------------------------------------
# Page: 5 -- Metadata
# ---------------------------------------------------------------------------

def page_metadata():
    st.title("Stage 5: Metadata Extraction")
    st.markdown(
        "Extracts detailed metadata for each contract type using field definitions "
        "from `metadata.csv` and prompt templates. Supports four contract types."
    )

    st.subheader("Configuration")
    cols = st.columns(3)
    cols[0].metric("LLM", "claude-sonnet-4-5")
    cols[1].metric("batch_size", "100")
    cols[2].metric("max_input_char", "400,000")

    st.subheader("Contract Types")

    type_labels = {
        "master_agreement": "Master Agreement",
        "amendment": "Amendment",
        "scope_of_work": "Scope of Work",
        "termination": "Termination",
    }

    tabs = st.tabs(list(type_labels.values()))

    for tab, (type_key, type_label) in zip(tabs, type_labels.items()):
        with tab:
            table_name = f"metadata_{type_key}"
            count = table_count(fqn(table_name))
            count_str = f"{count:,} rows" if count is not None else "-- rows"
            st.markdown(f"**Output table:** `{table_name}` ({count_str})")

            if connected:
                preview = table_preview(fqn(table_name))
                if preview is not None and len(preview) > 0:
                    st.dataframe(preview, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("**Prompt template**")
            st.code(read_prompt(type_key), language="markdown")

            st.markdown("---")
            st.markdown(f"**Fields ({len(METADATA.get(type_key, []))})**")

            fields = METADATA.get(type_key, [])
            if fields:
                header = "| Field | Description | Allowed Values |\n|---|---|---|\n"
                rows = []
                for f in fields:
                    enum = (f.get("enum_fields") or "").strip()
                    enum_display = f"`{enum}`" if enum else "--"
                    rows.append(
                        f"| `{f['metadata_name']}` | {f['metadata_description']} | {enum_display} |"
                    )
                st.markdown(header + "\n".join(rows))

    st.subheader("How Prompts Are Built")
    st.markdown(
        "Each metadata extraction call combines:\n"
        "1. The **base prompt** (`prompts/{type}.md`) setting the role and instructions\n"
        "2. The **field definitions** from `metadata.csv` appended as structured requirements\n"
        "3. The **contract text** from the assembled/classified tables\n\n"
        "The LLM returns a JSON object with one key per field from the metadata definition."
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

ROUTER = {
    "Pipeline Overview": page_overview,
    "1 -- Parse": page_parse,
    "2 -- Extract": page_extract,
    "3 -- Assemble": page_assemble,
    "4 -- Classify": page_classify,
    "5 -- Metadata": page_metadata,
}

ROUTER[page]()
