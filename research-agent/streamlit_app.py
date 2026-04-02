import streamlit as st

from agent import format_steps_text, run_agent


st.set_page_config(
    page_title="Research Assistant Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUGGESTED_QUERIES = [
    "What is 28.7 / 3.7 and what does the result mean?",
    "Search Wikipedia for the history of artificial intelligence. When was the term coined and by whom?",
    "Read the file data/sample_data.csv. Which country has the highest GDP growth rate?",
    "Read the file data/sample_data.csv. What is the average GDP across all 5 countries?",
]


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
            --bg: #f4f1ea;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-border: rgba(24, 34, 46, 0.10);
            --text: #18222e;
            --muted: #5c6977;
            --accent: #0f766e;
            --accent-soft: rgba(15, 118, 110, 0.10);
            --shadow: 0 14px 40px rgba(24, 34, 46, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.08), transparent 28%),
                radial-gradient(circle at top right, rgba(24, 34, 46, 0.05), transparent 24%),
                linear-gradient(180deg, #f8f6f1 0%, var(--bg) 100%);
            color: var(--text);
            font-family: "IBM Plex Sans", sans-serif;
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"],
        [data-testid="stMarkdownContainer"], [data-testid="stChatMessageContent"],
        [data-testid="stSidebar"], [data-testid="stHeader"],
        [data-testid="stToolbar"], [data-testid="stDecoration"] {
            color: var(--text) !important;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.08), transparent 28%),
                radial-gradient(circle at top right, rgba(24, 34, 46, 0.05), transparent 24%),
                linear-gradient(180deg, #f8f6f1 0%, var(--bg) 100%) !important;
        }

        [data-testid="stHeader"] {
            background: rgba(248, 246, 241, 0.94) !important;
            border-bottom: 1px solid rgba(24, 34, 46, 0.08);
        }

        [data-testid="stToolbar"] {
            background: transparent !important;
        }

        p, span, label, li, div, h1, h2, h3, h4, h5, h6 {
            color: var(--text);
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1240px;
        }

        [data-testid="stSidebar"] {
            background: rgba(249, 247, 242, 0.94);
            border-right: 1px solid rgba(24, 34, 46, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        .hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,255,255,0.72));
            border: 1px solid var(--panel-border);
            box-shadow: var(--shadow);
            border-radius: 24px;
            padding: 1.4rem 1.5rem 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 2rem;
            line-height: 1.05;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
            color: var(--text);
        }

        .hero-subtitle {
            color: var(--muted);
            font-size: 0.98rem;
            margin-bottom: 0.95rem;
            max-width: 760px;
        }

        .chip-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .chip {
            background: var(--accent-soft);
            color: var(--accent);
            border: 1px solid rgba(15, 118, 110, 0.16);
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .section-card {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 20px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(8px);
        }

        .status-card {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: var(--shadow);
            min-height: 112px;
        }

        .status-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .status-value {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        .status-subtext {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 0.35rem;
        }

        .empty-state {
            background: rgba(255,255,255,0.7);
            border: 1px dashed rgba(24, 34, 46, 0.16);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            color: var(--muted);
            margin-top: 0.6rem;
        }

        .stChatMessage {
            background: rgba(255,255,255,0.66);
            border: 1px solid rgba(24, 34, 46, 0.08);
            border-radius: 18px;
            padding: 0.35rem 0.2rem;
        }

        [data-testid="stChatMessageContent"] p,
        [data-testid="stChatMessageContent"] div,
        [data-testid="stChatMessageContent"] span {
            color: var(--text) !important;
        }

        .stExpander {
            border-radius: 16px;
            border: 1px solid rgba(24, 34, 46, 0.08);
            background: rgba(255,255,255,0.58);
        }

        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary span,
        [data-testid="stExpanderDetails"] {
            color: var(--text) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: transparent !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.6);
            border: 1px solid rgba(24, 34, 46, 0.08);
            border-radius: 12px;
            color: var(--text) !important;
            padding: 0.35rem 0.85rem;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(15, 118, 110, 0.10);
            border-color: rgba(15, 118, 110, 0.22);
            color: var(--accent) !important;
        }

        .stTextInput input, .stTextArea textarea, .stChatInput input {
            color: var(--text) !important;
            background: rgba(255,255,255,0.88) !important;
        }

        [data-testid="stChatInput"] {
            background: rgba(248, 246, 241, 0.96) !important;
        }

        [data-testid="stBottomBlockContainer"] {
            background: rgba(248, 246, 241, 0.96) !important;
            border-top: 1px solid rgba(24, 34, 46, 0.08);
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input,
        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] > div > div {
            background: rgba(255,255,255,0.96) !important;
            color: var(--text) !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        .stChatInput input::placeholder {
            color: var(--muted) !important;
        }

        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: var(--text) !important;
        }

        .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
            color: var(--text) !important;
        }

        code, pre, .stCodeBlock {
            font-family: "IBM Plex Mono", monospace !important;
        }

        pre, code, .stCodeBlock, [data-testid="stCodeBlock"], [data-testid="stCode"] {
            background: #f7f4ee !important;
            color: #1f2937 !important;
            border: 1px solid rgba(24, 34, 46, 0.08);
            border-radius: 14px !important;
        }

        [data-testid="stCodeBlock"] pre span,
        [data-testid="stCode"] pre span,
        pre span,
        code span {
            color: #1f2937 !important;
        }

        .element-container .stCodeBlock,
        .element-container pre {
            box-shadow: none !important;
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 12px;
            border: 1px solid rgba(24, 34, 46, 0.10);
            background: rgba(255,255,255,0.84);
            color: var(--text) !important;
        }

        .stButton > button:hover {
            border-color: rgba(15, 118, 110, 0.30);
            color: var(--accent);
        }

        [data-baseweb="select"] *, [role="tablist"] *, [role="tab"] *,
        button *, input, textarea {
            color: var(--text) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome. Ask a research question, compare figures, summarize a concept from Wikipedia, "
                    "or query the sample CSV file."
                ),
                "result": None,
            }
        ]
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None


def clear_chat():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Chat cleared. Ask the next question when ready.",
            "result": None,
        }
    ]
    st.session_state.last_result = None
    st.session_state.pending_query = None


def queue_query(query: str):
    st.session_state.pending_query = query


def tools_used_text(result: dict) -> str:
    return ", ".join(dict.fromkeys(step["action"] for step in result.get("steps", []))) or "None"


def render_header():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">Research Assistant Agent</div>
            <div class="hero-subtitle">
                A clean research workspace powered by Gemini and LangChain. Ask for current facts,
                background knowledge, calculations, or structured CSV analysis without leaving the page.
            </div>
            <div class="chip-row">
                <span class="chip">Gemini 2.5 Flash</span>
                <span class="chip">LangChain Agent</span>
                <span class="chip">DuckDuckGo Search</span>
                <span class="chip">Wikipedia</span>
                <span class="chip">Calculator</span>
                <span class="chip">CSV Reader</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_cards():
    result = st.session_state.last_result
    steps = result.get("num_steps", 0) if result else 0
    tools = tools_used_text(result) if result else "None"
    status = "Ready" if not result else ("Needs attention" if result.get("error") else "Completed")
    trace = "Captured" if result and result.get("debug_trace") else "Off"

    cols = st.columns(4)
    cards = [
        ("Status", status, "Current run state"),
        ("Steps", str(steps), "Intermediate tool actions"),
        ("Tools Used", tools, "Distinct tools used in the last run"),
        ("Debug Trace", trace, "Raw LangChain trace for the last run"),
    ]
    for col, (label, value, subtext) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="status-card">
                    <div class="status-label">{label}</div>
                    <div class="status-value">{value}</div>
                    <div class="status-subtext">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_sidebar():
    with st.sidebar:
        st.markdown("### Workspace")
        st.toggle("Capture debug trace", key="debug_mode")
        st.button("Clear chat", use_container_width=True, on_click=clear_chat)

        st.divider()
        st.markdown("### Suggested Queries")
        for idx, query in enumerate(SUGGESTED_QUERIES):
            st.button(
                query,
                key=f"suggested_{idx}",
                use_container_width=True,
                on_click=queue_query,
                args=(query,),
            )

        st.divider()
        st.markdown("### Guidance")
        st.markdown("Ask normal research questions, compare figures, or query the sample CSV file.")
        st.markdown("Enable debug mode before sending a query if you want the raw LangChain trace.")
        st.markdown("Use prompts like `Read the file data/sample_data.csv ...` for file-based analysis.")


def render_assistant_result(result: dict, debug_enabled_for_run: bool):
    if not result:
        return

    tabs = st.tabs(["Answer Details", "Tool Trace", "Raw Debug"])

    with tabs[0]:
        if result.get("error"):
            st.error(result["error"])
        else:
            st.caption(
                f"{result.get('num_steps', 0)} step(s) completed using {tools_used_text(result)}"
            )

    with tabs[1]:
        st.code(format_steps_text(result), language="text")

    with tabs[2]:
        if debug_enabled_for_run:
            debug_text = result.get("debug_trace", "").strip() or "No debug trace captured."
            st.code(debug_text, language="text")
        else:
            st.info("Debug capture was off for this response.")


def process_query(query: str):
    st.session_state.messages.append({"role": "user", "content": query, "result": None})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Running research agent..."):
            result = run_agent(query, capture_debug=st.session_state.debug_mode)
        st.markdown(result.get("answer", "No answer"))
        render_assistant_result(result, debug_enabled_for_run=st.session_state.debug_mode)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", "No answer"),
            "result": result,
            "debug_enabled": st.session_state.debug_mode,
        }
    )
    st.session_state.last_result = result


def render_chat_history():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Conversation")
    if len(st.session_state.messages) == 1 and st.session_state.messages[0]["role"] == "assistant":
        st.markdown(
            """
            <div class="empty-state">
                Start with a direct question, a Wikipedia lookup, a calculation, or a CSV analysis request.
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("result"):
                render_assistant_result(
                    message["result"],
                    debug_enabled_for_run=message.get("debug_enabled", False),
                )
    st.markdown("</div>", unsafe_allow_html=True)


apply_theme()
init_state()
render_sidebar()
render_header()
render_status_cards()
render_chat_history()

prompt = st.chat_input("Ask a research question")
pending_query = st.session_state.pending_query
if pending_query:
    st.session_state.pending_query = None
    process_query(pending_query)
    st.rerun()

if prompt:
    process_query(prompt)
    st.rerun()
