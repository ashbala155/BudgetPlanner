from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from budget_agent_backend import (
    BudgetPlan,
    authenticate_user,
    build_agent_response,
    build_budget_context,
    build_projection,
    build_recommendations,
    default_category_budget,
    fallback_chat_reply,
    generate_openai_budget_reply,
    has_registered_users,
    load_budget_history,
    merge_category_targets,
    parse_transactions_csv,
    register_user,
    save_budget_snapshot,
    suggest_budget,
    summarize_transactions,
)


st.set_page_config(
    page_title="Budget Planning AI Agent",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600;700;800&display=swap');

        .stApp {
            background:
                linear-gradient(rgba(248, 250, 252, 0.78), rgba(236, 253, 245, 0.82)),
                url("https://images.unsplash.com/vector-1760337188246-8bb2a803fdb6?q=80&w=1433&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            font-family: 'DM Sans', sans-serif;
            color: #0f172a;
        }
        .stApp p, .stApp label, .stApp span, .stApp div, .stApp input, .stApp textarea, .stApp button {
            font-family: 'DM Sans', sans-serif;
        }
        .stApp h1, .stApp h2, .stApp h3 {
            font-family: 'Playfair Display', serif;
            letter-spacing: 0.01em;
        }
        .stApp h1 {
            background: linear-gradient(90deg, #0f172a 0%, #0f766e 40%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stApp h2, .stApp h3 {
            color: #14532d;
        }
        .hero-card {
            padding: 1.5rem;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.25);
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
        }
        .panel-card {
            padding: 1rem 1.2rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.22);
        }
        .insight-card {
            padding: 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(240, 253, 250, 0.95), rgba(220, 252, 231, 0.95));
            border: 1px solid rgba(34, 197, 94, 0.16);
        }
        .tag {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            margin: 0.15rem;
            border-radius: 999px;
            font-size: 0.85rem;
            background: rgba(186, 230, 253, 0.65);
            color: #0f172a;
            font-weight: 700;
            box-shadow: 0 8px 20px rgba(14, 165, 233, 0.12);
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Playfair Display', serif;
            color: #7c2d12;
        }
        div[data-testid="stMetricLabel"] {
            font-family: 'DM Sans', sans-serif;
            color: #14532d;
            font-weight: 700;
        }
        div[data-testid="stChatMessage"] {
            backdrop-filter: blur(8px);
            border-radius: 18px;
        }
        .stCaption {
            color: #155e75;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_secret_value(section: str, key: str) -> str:
    section_value: Any = st.secrets.get(section, {})
    if hasattr(section_value, "get"):
        return str(section_value.get(key, "")).strip()
    return ""


def reset_user_session_state() -> None:
    for key in [
        "budget_messages",
        "category_budget_df",
        "category_editor",
        "pending_budget_prompt",
    ]:
        st.session_state.pop(key, None)


def login_gate() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = ""

    if st.session_state.authenticated:
        return

    any_users_exist = has_registered_users()
    st.markdown(
        """
        <div class="hero-card">
            <p style="margin-bottom:0.35rem; color:#475569; font-size:0.95rem;">Secure access</p>
            <h1 style="margin-bottom:0.2rem; color:#0f172a;">Access Budget Planning AI Agent</h1>
            <p style="font-size:1.0rem; color:#334155; max-width:720px;">
                Create an account inside the app, then sign in to keep your budget history tied to your profile.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        if not any_users_exist:
            st.info("No user accounts exist yet. Create the first account in the Create account tab.")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                authenticated_username = authenticate_user(username, password)
                if authenticated_username:
                    st.session_state.authenticated = True
                    st.session_state.current_user = authenticated_username
                    reset_user_session_state()
                    st.rerun()
                else:
                    st.error("Those credentials did not match an existing account.")

    with sign_up_tab:
        st.caption("Usernames should use lowercase letters, numbers, dots, dashes, or underscores.")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input("Choose a password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_password_confirm")
            signup_submitted = st.form_submit_button("Create account", use_container_width=True)
            if signup_submitted:
                if new_password != confirm_password:
                    st.error("The passwords did not match.")
                else:
                    try:
                        created_username = register_user(new_username, new_password)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state.authenticated = True
                        st.session_state.current_user = created_username
                        reset_user_session_state()
                        st.success("Account created. You are now signed in.")
                        st.rerun()
    st.stop()


def render_header(username: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <p style="margin-bottom:0.35rem; color:#475569; font-size:0.95rem;">Personal finance assistant</p>
            <h1 style="margin-bottom:0.2rem; color:#0f172a;">Budget Planning AI Agent</h1>
            <p style="font-size:1.05rem; color:#334155; max-width:760px;">
                Welcome, {username}. Build a monthly budget, upload transactions, track category drift,
                save snapshots to your budget history, and ask an OpenAI-powered coach for tailored guidance.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[float, float, float, float, float, str, str]:
    st.sidebar.title("Your Money Inputs")
    monthly_income = st.sidebar.number_input("Monthly take-home income", min_value=0.0, value=5000.0, step=100.0)
    fixed_costs = st.sidebar.number_input("Fixed monthly costs", min_value=0.0, value=2200.0, step=50.0)
    variable_costs = st.sidebar.number_input("Variable monthly spending", min_value=0.0, value=1100.0, step=50.0)
    debt_payments = st.sidebar.number_input("Minimum debt payments", min_value=0.0, value=300.0, step=25.0)
    savings_goal = st.sidebar.number_input("Savings goal", min_value=0.0, value=6000.0, step=100.0)
    priority = st.sidebar.selectbox(
        "Primary goal",
        ["Balanced plan", "Aggressive saving", "Debt payoff", "Low-stress budget"],
    )

    openai_model = (
        get_secret_value("openai", "model")
        or os.getenv("OPENAI_MODEL", "").strip()
        or "gpt-4.1-mini"
    )

    st.sidebar.markdown("### Features")
    for tag in ["Login", "CSV upload", "Budget history", "OpenAI coaching"]:
        st.sidebar.markdown(f'<span class="tag">{tag}</span>', unsafe_allow_html=True)

    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        reset_user_session_state()
        st.rerun()

    return monthly_income, fixed_costs, variable_costs, debt_payments, savings_goal, priority, openai_model


def render_budget_summary(plan: BudgetPlan) -> None:
    st.subheader("Recommended Budget")
    metrics = st.columns(5)
    values = [
        ("Essentials", f"${plan.essentials:,.0f}"),
        ("Lifestyle", f"${plan.lifestyle:,.0f}"),
        ("Savings", f"${plan.savings:,.0f}"),
        ("Debt", f"${plan.debt:,.0f}"),
        ("Buffer", f"${plan.leftover:,.0f}"),
    ]
    for col, (label, value) in zip(metrics, values):
        with col:
            st.metric(label, value)

    allocation_df = pd.DataFrame(
        {
            "Category": ["Essentials", "Lifestyle", "Savings", "Debt", "Buffer"],
            "Amount": [plan.essentials, plan.lifestyle, plan.savings, plan.debt, max(plan.leftover, 0.0)],
        }
    )
    fig = px.pie(
        allocation_df,
        names="Category",
        values="Amount",
        hole=0.55,
        color="Category",
        color_discrete_map={
            "Essentials": "#0ea5e9",
            "Lifestyle": "#22c55e",
            "Savings": "#f97316",
            "Debt": "#8b5cf6",
            "Buffer": "#64748b",
        },
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_uploaded_expenses() -> pd.DataFrame:
    st.subheader("Upload Expenses")
    st.caption("Upload a CSV with columns such as amount, category, and date to compare actual spending against your plan.")
    uploaded_file = st.file_uploader("Upload transaction CSV", type=["csv"])

    if uploaded_file is None:
        return pd.DataFrame(columns=["Category", "Actual", "Monthly estimate", "Share %"])

    try:
        transactions_df = parse_transactions_csv(uploaded_file)
        summary_df = summarize_transactions(transactions_df)
    except ValueError as exc:
        st.error(str(exc))
        return pd.DataFrame(columns=["Category", "Actual", "Monthly estimate", "Share %"])

    st.success(f"Loaded {len(transactions_df)} expense rows from {uploaded_file.name}.")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    return summary_df


def render_category_budget(actuals_df: pd.DataFrame) -> pd.DataFrame:
    st.subheader("Expense Categories")
    st.caption("Adjust planned category limits, then compare them with actual monthly estimates from your uploaded CSV.")

    if "category_budget_df" not in st.session_state:
        st.session_state.category_budget_df = default_category_budget()

    merged_df = merge_category_targets(st.session_state.category_budget_df, actuals_df)
    edited_df = st.data_editor(
        merged_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Category": st.column_config.TextColumn(required=True),
            "Type": st.column_config.SelectboxColumn(options=["Essential", "Flexible", "Debt", "Savings"]),
            "Planned": st.column_config.NumberColumn(format="$%.2f", min_value=0.0),
            "Actual": st.column_config.NumberColumn(format="$%.2f", disabled=True),
            "Variance": st.column_config.NumberColumn(format="$%.2f", disabled=True),
        },
        key="category_editor",
    )
    edited_df["Actual"] = edited_df["Actual"].fillna(0.0)
    edited_df["Variance"] = edited_df["Planned"].fillna(0.0) - edited_df["Actual"]
    st.session_state.category_budget_df = edited_df[["Category", "Type", "Planned"]]

    over_budget_df = edited_df.loc[edited_df["Variance"] < 0].sort_values(by="Variance")
    if over_budget_df.empty:
        st.info("No categories are currently over budget.")
    else:
        top_row = over_budget_df.iloc[0]
        st.warning(
            f"{top_row['Category']} is currently the most over-budget category at ${abs(top_row['Variance']):,.0f} above target."
        )
    return edited_df


def render_projection(projection_df: pd.DataFrame) -> None:
    st.subheader("12-Month Projection")
    fig = px.line(
        projection_df,
        x="Month",
        y=["Savings built", "Debt paid"],
        markers=True,
        color_discrete_sequence=["#f97316", "#8b5cf6"],
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_history(username: str, history_df: pd.DataFrame) -> None:
    st.subheader("Budget History")
    if history_df.empty:
        st.info("No saved budget snapshots yet. Save the current plan to start building history.")
        return

    display_df = history_df.copy()
    display_df["saved_at"] = display_df["saved_at"].dt.strftime("%Y-%m-%d %H:%M")

    history_chart_df = history_df.rename(columns={"saved_at": "Saved at"})
    fig = px.line(
        history_chart_df,
        x="Saved at",
        y=["savings", "leftover", "debt"],
        markers=True,
        color_discrete_sequence=["#f97316", "#64748b", "#8b5cf6"],
    )
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        display_df[
            ["saved_at", "priority", "income", "savings", "debt", "leftover", "savings_rate"]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Saved snapshots for {username}.")


def render_agent_chat(
    api_key: str,
    model: str,
    summary: str,
    recommendations: list[str],
    budget_context: dict[str, object],
    plan: BudgetPlan,
    category_df: pd.DataFrame,
) -> None:
    st.subheader("Ask the Budget Agent")
    if api_key:
        st.caption(f"OpenAI chat is enabled with model `{model}`.")
    else:
        st.caption("OpenAI chat is not configured yet, so the app is using local fallback answers.")

    if "budget_messages" not in st.session_state:
        st.session_state.budget_messages = [{"role": "assistant", "content": summary}]

    for message in st.session_state.budget_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    quick_questions = [
        "How can I save faster?",
        "Where should I cut spending first?",
        "Should I focus on debt or savings?",
    ]
    cols = st.columns(3)
    for col, question in zip(cols, quick_questions):
        with col:
            if st.button(question, use_container_width=True):
                st.session_state.pending_budget_prompt = question

    prompt = st.chat_input("Ask about savings, debt, categories, or tradeoffs")
    queued_prompt = st.session_state.pop("pending_budget_prompt", None)
    active_prompt = prompt or queued_prompt

    if not active_prompt:
        return

    st.session_state.budget_messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.write(active_prompt)

    try:
        if api_key:
            reply = generate_openai_budget_reply(
                api_key=api_key,
                model=model,
                messages=st.session_state.budget_messages,
                budget_context=budget_context,
            )
        else:
            reply = fallback_chat_reply(active_prompt, plan, recommendations, category_df)
    except Exception as exc:
        reply = (
            "I could not reach the OpenAI API right now, so I switched to a local fallback answer. "
            f"Details: {exc}"
        )

    st.session_state.budget_messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)


def main() -> None:
    login_gate()
    username = st.session_state.current_user
    api_key = get_secret_value("openai", "api_key") or os.getenv("OPENAI_API_KEY", "").strip()

    render_header(username)
    (
        monthly_income,
        fixed_costs,
        variable_costs,
        debt_payments,
        savings_goal,
        priority,
        openai_model,
    ) = render_sidebar()

    if monthly_income <= 0:
        st.warning("Add your monthly take-home income to generate a plan.")
        return

    plan = suggest_budget(
        monthly_income=monthly_income,
        fixed_costs=fixed_costs,
        variable_costs=variable_costs,
        debt_payments=debt_payments,
        savings_goal=savings_goal,
        priority=priority,
    )
    summary = build_agent_response(plan, savings_goal, priority)
    recommendations = build_recommendations(plan, fixed_costs, variable_costs)
    projection_df = build_projection(plan, savings_goal)
    uploaded_actuals_df = render_uploaded_expenses()
    category_df = render_category_budget(uploaded_actuals_df)
    history_df = load_budget_history(username)
    budget_context = build_budget_context(
        plan=plan,
        fixed_costs=fixed_costs,
        variable_costs=variable_costs,
        debt_payments=debt_payments,
        savings_goal=savings_goal,
        priority=priority,
        category_df=category_df,
        history_df=history_df,
    )

    left, right = st.columns([1.15, 1])
    with left:
        render_budget_summary(plan)
    with right:
        st.subheader("Agent Recommendation")
        st.markdown(f'<div class="insight-card"><p>{summary}</p></div>', unsafe_allow_html=True)
        st.markdown("### Next best moves")
        for item in recommendations:
            st.write(f"- {item}")
        if st.button("Save budget snapshot", use_container_width=True):
            save_budget_snapshot(
                username=username,
                plan=plan,
                fixed_costs=fixed_costs,
                variable_costs=variable_costs,
                debt_payments=debt_payments,
                savings_goal=savings_goal,
                priority=priority,
            )
            st.success("Saved this budget snapshot to history.")
            st.rerun()
        st.caption("This app is for planning and education, not regulated financial advice.")

    st.divider()
    render_projection(projection_df)
    st.divider()
    render_history(username, history_df)
    st.divider()
    render_agent_chat(
        api_key=api_key,
        model=openai_model,
        summary=summary,
        recommendations=recommendations,
        budget_context=budget_context,
        plan=plan,
        category_df=category_df,
    )


if __name__ == "__main__":
    main()
