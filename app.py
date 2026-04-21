from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from portfolio_agent import CASE_STUDY, PROFILE, PROJECTS, SKILLS, answer_prompt, recruiter_pitch


st.set_page_config(
    page_title="AI Portfolio Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(29, 78, 216, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(249, 115, 22, 0.16), transparent 28%),
                linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        }
        .hero-card {
            padding: 1.5rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.25);
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
        }
        .section-card {
            padding: 1rem 1.2rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(148, 163, 184, 0.24);
            min-height: 215px;
        }
        .metric-card {
            padding: 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(224,231,255,0.88));
            border: 1px solid rgba(99, 102, 241, 0.12);
            text-align: center;
        }
        .pill {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            margin: 0.2rem;
            border-radius: 999px;
            font-size: 0.85rem;
            color: #0f172a;
            background: rgba(191, 219, 254, 0.7);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <p style="margin-bottom:0.3rem; color:#475569; font-size:0.95rem;">Interactive AI portfolio agent</p>
            <h1 style="margin-bottom:0.2rem; color:#0f172a;">{PROFILE["name"]}</h1>
            <h3 style="margin-top:0; color:#1d4ed8;">{PROFILE["title"]}</h3>
            <p style="font-size:1.05rem; color:#334155; max-width:780px;">{PROFILE["pitch"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.title("Agent Controls")
    persona = st.sidebar.selectbox(
        "Audience",
        ["Recruiter", "Hiring Manager", "Technical Interviewer", "Founder / Stakeholder"],
    )
    focus = st.sidebar.radio(
        "Primary emphasis",
        ["Balanced portfolio", "Machine learning", "Business impact", "AI agent design"],
    )
    st.sidebar.markdown("### Core strengths")
    for item in PROFILE["strengths"]:
        st.sidebar.markdown(f"- {item}")
    st.sidebar.info(
        f"Current mode: {persona}\n\nFocus: {focus}. Use the chat panel to tailor how the agent presents the profile."
    )


def render_skill_overview() -> None:
    st.subheader("Skill Snapshot")
    cols = st.columns(len(SKILLS))
    for col, skill in zip(cols, SKILLS):
        with col:
            st.markdown(f'<div class="section-card"><h4>{skill.name}</h4><p>{skill.summary}</p>', unsafe_allow_html=True)
            st.progress(skill.level / 100)
            st.caption(f"{skill.level}/100")
            for tool in skill.tools:
                st.markdown(f'<span class="pill">{tool}</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


def render_project_showcase() -> None:
    st.subheader("Portfolio Projects")
    for project in PROJECTS:
        with st.container():
            st.markdown(f"### {project.name}")
            left, right = st.columns([2, 1])
            with left:
                st.write(project.headline)
                st.write(f"**Business impact:** {project.business_impact}")
                for item in project.highlights:
                    st.write(f"- {item}")
            with right:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.write("**Tech stack**")
                for tool in project.stack:
                    st.markdown(f'<span class="pill">{tool}</span>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


def render_case_study() -> None:
    st.subheader("Mini Case Study")
    metric_cols = st.columns(5)
    labels = [
        ("Rows analyzed", f"{CASE_STUDY['dataset_rows']:,}"),
        ("Features", str(CASE_STUDY["features"])),
        ("Baseline AUC", f"{CASE_STUDY['baseline_auc']:.2f}"),
        ("Production AUC", f"{CASE_STUDY['production_auc']:.2f}"),
        ("Retention Lift", f"{CASE_STUDY['retention_gain']:.1f}%"),
    ]
    for col, (label, value) in zip(metric_cols, labels):
        with col:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label, value)
            st.markdown("</div>", unsafe_allow_html=True)

    chart_df = pd.DataFrame(
        {
            "Stage": ["Baseline model", "Feature engineering", "Tuned ensemble", "Production thresholding"],
            "AUC": [0.74, 0.81, 0.87, 0.89],
        }
    )
    fig = px.line(
        chart_df,
        x="Stage",
        y="AUC",
        markers=True,
        line_shape="spline",
        color_discrete_sequence=["#ea580c"],
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.6)",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_chat_agent() -> None:
    st.subheader("Ask the Portfolio Agent")
    st.caption("Try prompts like: 'How would you present your churn model?', 'What AI skills do you bring?', or 'How do you think about deployment?'")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": recruiter_pitch(),
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    quick_prompt_cols = st.columns(3)
    quick_prompts = [
        "What ML skills stand out here?",
        "How would you explain your business impact?",
        "Tell me about your AI agent experience.",
    ]
    for col, prompt in zip(quick_prompt_cols, quick_prompts):
        with col:
            if st.button(prompt, use_container_width=True):
                st.session_state.pending_prompt = prompt

    user_prompt = st.chat_input("Ask the agent about projects, modeling, AI, or deployment")
    queued_prompt = st.session_state.pop("pending_prompt", None)
    active_prompt = user_prompt or queued_prompt

    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.write(active_prompt)

        response = answer_prompt(active_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)


def main() -> None:
    render_sidebar()
    render_header()

    top_left, top_right = st.columns([1.25, 1])
    with top_left:
        render_skill_overview()
    with top_right:
        st.subheader("Recruiter Summary")
        st.markdown(f'<div class="section-card"><p>{recruiter_pitch()}</p></div>', unsafe_allow_html=True)

    st.divider()
    render_project_showcase()
    st.divider()
    render_case_study()
    st.divider()
    render_chat_agent()


if __name__ == "__main__":
    main()
