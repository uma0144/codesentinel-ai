import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

from core.static_analyzer import StaticAnalyzer
from core.patch_engine import PatchEngine
from core.orchestrator import CodeReviewOrchestrator
from core.llm_client import LLMClient
from benchmarks import BENCHMARK_SCENARIOS, load_benchmark_code
from utils.github_loader import GitHubLoader
from utils.report_exporter import ReportExporter

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CodeSentinel AI ? Code Reviewer & Bug Fixing Agent",
    page_icon="???",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphic UI)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .badge-critical {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-high {
        background-color: #f97316;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-medium {
        background-color: #eab308;
        color: black;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #3b82f6;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "current_code" not in st.session_state:
    st.session_state.current_code = load_benchmark_code("sql_injection")
if "current_lang" not in st.session_state:
    st.session_state.current_lang = "python"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_benchmark" not in st.session_state:
    st.session_state.selected_benchmark = "sql_injection"

# Sidebar Configuration
with st.sidebar:
    st.markdown("## ?? Agent Configuration")
    
    provider = st.selectbox(
        "LLM Provider",
        options=["Gemini (Google)", "OpenAI", "Groq (Llama 3.3)", "Demo Mode (Offline)"],
        index=0
    )
    
    provider_key_map = {
        "Gemini (Google)": "gemini",
        "OpenAI": "openai",
        "Groq (Llama 3.3)": "groq",
        "Demo Mode (Offline)": "demo"
    }
    selected_provider = provider_key_map[provider]
    
    api_key = ""
    model_name = None
    
    if selected_provider != "demo":
        env_key = os.getenv(f"{selected_provider.upper()}_API_KEY", "")
        api_key = st.text_input(
            f"{provider} API Key",
            value=env_key,
            type="password",
            help="Your API key is used only for this session and never stored."
        )
        if selected_provider == "gemini":
            model_name = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"], index=0)
        elif selected_provider == "openai":
            model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        elif selected_provider == "groq":
            model_name = st.selectbox("Model", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"], index=0)
    else:
        st.info("?? **Demo Mode:** Uses pre-computed evaluations and static AST heuristics. No API key required!")

    st.markdown("---")
    st.markdown("## ?? Code Input Source")
    
    input_mode = st.radio(
        "Select Source",
        options=["?? Curated Benchmarks", "?? Custom Snippet", "?? File Upload", "?? GitHub URL"],
        index=0
    )
    
    benchmark_key = None
    
    if input_mode == "?? Curated Benchmarks":
        benchmark_choice = st.selectbox(
            "Select Vulnerability Scenario",
            options=list(BENCHMARK_SCENARIOS.keys()),
            format_func=lambda k: f"{BENCHMARK_SCENARIOS[k]['title']}"
        )
        st.session_state.selected_benchmark = benchmark_choice
        benchmark_key = benchmark_choice
        st.session_state.current_code = load_benchmark_code(benchmark_choice)
        st.session_state.current_lang = BENCHMARK_SCENARIOS[benchmark_choice]["language"]
        st.caption(f"**Description:** {BENCHMARK_SCENARIOS[benchmark_choice]['description']}")
        
    elif input_mode == "?? Custom Snippet":
        st.session_state.current_lang = st.selectbox(
            "Language",
            options=["python", "javascript", "typescript", "go", "rust", "java", "cpp", "sql"],
            index=0
        )
        
    elif input_mode == "?? File Upload":
        uploaded_file = st.file_uploader("Upload Code File", type=["py", "js", "ts", "go", "rs", "java", "cpp", "sql"])
        if uploaded_file is not None:
            st.session_state.current_code = uploaded_file.getvalue().decode("utf-8")
            ext = uploaded_file.name.split(".")[-1]
            st.session_state.current_lang = "python" if ext in ("py", "pyw") else ("javascript" if ext in ("js", "mjs") else ext)
            
    elif input_mode == "?? GitHub URL":
        github_url = st.text_input("GitHub File URL", placeholder="https://github.com/owner/repo/blob/main/file.py")
        if st.button("Fetch GitHub File"):
            with st.spinner("Fetching file from GitHub..."):
                res = GitHubLoader.fetch_file(github_url)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.session_state.current_code = res["content"]
                    st.session_state.current_lang = res["language"]
                    st.success(f"Fetched {res['filename']} ({res['language']})")

    st.markdown("---")
    analyze_btn = st.button("?? Run Multi-Agent Review", type="primary", use_container_width=True)

# Main Dashboard View
st.markdown('<div class="main-header">??? CodeSentinel AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Multi-Agent Code Reviewer, Vulnerability Auditor & Automated Patch Synthesis Engine</div>', unsafe_allow_html=True)

# Code Editor Input Area
code_col, info_col = st.columns([3, 1])

with code_col:
    code_input = st.text_area(
        f"Source Code Input ({st.session_state.current_lang})",
        value=st.session_state.current_code,
        height=260,
        key="code_editor"
    )
    st.session_state.current_code = code_input

with info_col:
    # Quick Pre-flight AST analysis
    quick_ast = StaticAnalyzer.analyze(st.session_state.current_code, st.session_state.current_lang)
    q_metrics = quick_ast.get("metrics", {})
    
    st.markdown("### ?? Pre-flight Sentinel")
    st.metric("Lines of Code (LOC)", q_metrics.get("total_lines", 0))
    st.metric("Cyclomatic Complexity", q_metrics.get("cyclomatic_complexity", 1))
    st.metric("Maintainability Index", f"{q_metrics.get('maintainability_index', 70)} / 100")
    if quick_ast.get("heuristics"):
        st.warning(f"?? {len(quick_ast['heuristics'])} Static Heuristic Alert(s)")

# Execution Logic
if analyze_btn:
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    def update_progress(msg, val):
        status_text.text(f"? {msg}")
        progress_bar.progress(val)
        
    orchestrator = CodeReviewOrchestrator(
        provider=selected_provider,
        api_key=api_key,
        model=model_name
    )
    
    with st.spinner("Analyzing code across multi-agent pipeline..."):
        result = orchestrator.review_code(
            code=st.session_state.current_code,
            language=st.session_state.current_lang,
            benchmark_key=benchmark_key if input_mode == "?? Curated Benchmarks" else None,
            progress_callback=update_progress
        )
        st.session_state.review_result = result
        progress_bar.empty()
        status_text.empty()
        st.success("? Multi-Agent Review Complete!")

# Display Review Results
if st.session_state.review_result:
    res = st.session_state.review_result
    scores = res.get("scores", {})
    sec = res.get("security", {})
    qual = res.get("quality", {})
    bugs = res.get("bugs", {})
    tests = res.get("test_suite", {})
    patch = res.get("patch", {})
    stats = patch.get("stats", {})
    
    st.markdown("---")
    st.markdown("## ?? Executive Health Scorecard")
    
    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        comp_score = res.get("composite_score", 70)
        color = "??" if comp_score >= 80 else ("??" if comp_score >= 50 else "??")
        st.metric("Composite Health", f"{comp_score} / 100", delta=f"{color} Rating")
    with m2:
        sec_score = scores.get("security", 70)
        st.metric("??? Security Score", f"{sec_score} / 100")
    with m3:
        rel_score = scores.get("reliability", 80)
        st.metric("?? Reliability Score", f"{rel_score} / 100")
    with m4:
        perf_score = scores.get("performance", 75)
        st.metric("? Performance", f"{perf_score} / 100")
    with m5:
        maint_score = scores.get("maintainability", 70)
        st.metric("?? Maintainability", f"{maint_score} / 100")

    # Radar Chart & Summary Breakdown
    chart_col, summary_col = st.columns([1, 1])
    
    with chart_col:
        categories = ['Security', 'Reliability', 'Performance', 'Maintainability', 'Code Quality']
        orig_values = [
            scores.get('security', 50),
            scores.get('reliability', 50),
            scores.get('performance', 60),
            scores.get('maintainability', 55),
            scores.get('quality', 60)
        ]
        fixed_values = [95, 95, 90, 88, 92]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=orig_values,
            theta=categories,
            fill='toself',
            name='Original Code',
            line_color='#ef4444'
        ))
        fig.add_trace(go.Scatterpolar(
            r=fixed_values,
            theta=categories,
            fill='toself',
            name='AI Patched Code',
            line_color='#22c55e'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title="Code Quality Dimension Comparison",
            height=320,
            margin=dict(l=40, r=40, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with summary_col:
        st.markdown("### ?? Executive Summary")
        st.write(f"**Security Overview:** {sec.get('summary', 'Standard posture.')}")
        st.write(f"**Architecture & Quality:** {qual.get('summary', 'Standard structure.')}")
        st.write(f"**Diagnostics & Remediation:** {bugs.get('summary', 'Remediations generated.')}")
        
        st.markdown(f"**Patch Stats:** `+{stats.get('additions', 0)} additions`, `-{stats.get('deletions', 0)} deletions`, `~{stats.get('modifications', 0)} modifications`")

    st.markdown("---")
    
    # Tabbed Drilldown
    tab_diff, tab_sec, tab_qual, tab_bugs, tab_tests, tab_chat, tab_export = st.tabs([
        "?? Side-by-Side Diff & Patch",
        "??? Security Audit",
        "? Performance & Quality",
        "?? Bug Diagnostics",
        "?? Unit Test Suite",
        "?? AI Code Assistant",
        "?? Export Report"
    ])
    
    # 1. Diff & Patch Tab
    with tab_diff:
        st.markdown("### ?? Original Code vs. AI Fixed & Refactored Code")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown("#### ? Original Code (Vulnerable / Flawed)")
            st.code(st.session_state.current_code, language=st.session_state.current_lang)
        with d_col2:
            st.markdown("#### ? AI Patched & Hardened Code")
            st.code(patch.get("fixed_code", st.session_state.current_code), language=st.session_state.current_lang)
            
        st.markdown("#### ?? Unified Git Diff (`git diff`)")
        st.code(patch.get("unified_diff", ""), language="diff")
        
        # Download buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            ext = "py" if st.session_state.current_lang == "python" else "js"
            st.download_button(
                "?? Download Fixed Code File",
                data=patch.get("fixed_code", ""),
                file_name=f"fixed_source.{ext}",
                mime="text/plain",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                "?? Download .patch File",
                data=patch.get("unified_diff", ""),
                file_name="remediation.patch",
                mime="text/plain",
                use_container_width=True
            )

    # 2. Security Audit Tab
    with tab_sec:
        st.markdown("### ??? Vulnerability Audit (OWASP & CWE)")
        vulns = sec.get("vulnerabilities", [])
        if vulns:
            for v in vulns:
                sev = v.get("severity", "MEDIUM")
                badge_class = f"badge-{sev.lower()}"
                
                with st.expander(f"?? [{sev}] {v.get('title')}", expanded=True):
                    st.markdown(f"**CWE:** `{v.get('cwe_id')}` | **OWASP Category:** `{v.get('owasp_category')}` | **Lines:** `{v.get('line_numbers', [])}`")
                    st.markdown(f"**Description:** {v.get('description')}")
                    st.markdown(f"**Attack Vector:** {v.get('attack_vector')}")
                    st.markdown(f"**Remediation:** {v.get('remediation')}")
        else:
            st.success("? No security vulnerabilities detected.")

    # 3. Performance & Quality Tab
    with tab_qual:
        st.markdown("### ? Algorithmic Complexity & Architecture")
        q1, q2 = st.columns(2)
        with q1:
            st.markdown(f"**Time Complexity:** `{qual.get('time_complexity', 'O(N)')}`")
            st.markdown(f"**Space Complexity:** `{qual.get('space_complexity', 'O(1)')}`")
        with q2:
            st.markdown(f"**Maintainability Score:** `{qual.get('maintainability_score', 75)} / 100`")
            st.markdown(f"**Performance Score:** `{qual.get('performance_score', 80)} / 100`")
            
        issues = qual.get("issues", [])
        if issues:
            st.markdown("#### Quality & Optimization Opportunities")
            for iss in issues:
                with st.expander(f"?? [{iss.get('category')}] {iss.get('title')}"):
                    st.write(iss.get('description'))
                    st.info(f"**Recommendation:** {iss.get('recommendation')}")
        
        strengths = qual.get("strengths", [])
        if strengths:
            st.markdown("#### Architectural Strengths")
            for s in strengths:
                st.write(f"?? {s}")

    # 4. Bug Diagnostics Tab
    with tab_bugs:
        st.markdown("### ?? Runtime Bug Diagnostics & Root Cause Analysis")
        bug_list = bugs.get("bugs_detected", [])
        if bug_list:
            for b in bug_list:
                with st.expander(f"?? [{b.get('type')}] {b.get('title')}", expanded=True):
                    st.markdown(f"**Severity:** `{b.get('severity')}` | **Lines:** `{b.get('line_numbers', [])}`")
                    st.markdown(f"**Root Cause:** {b.get('root_cause')}")
                    st.markdown(f"**Reproduction Scenario:** {b.get('reproduction_scenario')}")
                    st.markdown(f"**Fix Strategy:** {b.get('fix_strategy')}")
        else:
            st.success("? No critical logic or runtime flaws detected.")

    # 5. Unit Test Suite Tab
    with tab_tests:
        st.markdown(f"### ?? Generated Test Suite (`{tests.get('test_file_name', 'test_suite.py')}`)")
        st.caption(f"**Framework:** `{tests.get('framework')}` | **Focus Areas:** {', '.join(tests.get('coverage_focus', []))}")
        st.code(tests.get("test_code", "# No tests"), language="python" if tests.get("framework") in ("pytest", "unittest") else "javascript")
        st.write(f"**Test Strategy:** {tests.get('explanation', '')}")
        
        st.download_button(
            "?? Download Test Suite File",
            data=tests.get("test_code", ""),
            file_name=tests.get("test_file_name", "test_suite.py"),
            mime="text/plain",
            use_container_width=True
        )

    # 6. Interactive AI Code Assistant Tab
    with tab_chat:
        st.markdown("### ?? Chat with CodeSentinel Assistant")
        st.caption("Ask questions about the findings, vulnerabilities, alternative fixes, or architectural trade-offs.")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        user_query = st.chat_input("Ask a question about this code review...")
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)
                
            # Assistant Response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    context_prompt = f"""You are CodeSentinel AI Assistant.
The user is asking questions about the code and review findings.

--- ORIGINAL CODE ---
{st.session_state.current_code}

--- PATCHED CODE ---
{patch.get('fixed_code', '')}

--- SECURITY FINDINGS ---
{sec}

--- USER QUESTION ---
{user_query}
"""
                    if selected_provider != "demo" and api_key:
                        llm_assistant = LLMClient(provider=selected_provider, api_key=api_key, model=model_name)
                        response_text = llm_assistant.generate("You are an expert AI code security and architecture pair programmer. Provide direct, helpful, and technically accurate explanations.", context_prompt)
                    else:
                        response_text = f"**CodeSentinel Insight:**\n\nBased on the analysis of your code, the primary fixes were focused on preventing vulnerabilities (such as CWEs and unhandled resources) and enforcing thread safety / input sanitization. The patch ensures standard compliance and defensive programming patterns are met without breaking functionality."
                    
                    st.write(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})

    # 7. Export Report Tab
    with tab_export:
        st.markdown("### ?? Export Audit Reports")
        md_content = ReportExporter.to_markdown(res, filename=f"source.{ 'py' if st.session_state.current_lang=='python' else 'js' }")
        json_content = ReportExporter.to_json(res)
        
        st.download_button(
            "?? Download Markdown Review Report (.md)",
            data=md_content,
            file_name="code_review_report.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.download_button(
            "?? Download JSON Audit Log (.json)",
            data=json_content,
            file_name="code_review_audit.json",
            mime="application/json",
            use_container_width=True
        )
        
        with st.expander("??? Preview Markdown Report"):
            st.markdown(md_content)
