from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"
HISTORY_PATH = DATA_DIR / "budget_history.json"


@dataclass(frozen=True)
class BudgetPlan:
    income: float
    essentials: float
    lifestyle: float
    savings: float
    debt: float
    leftover: float
    emergency_months: float
    savings_rate: float


def suggest_budget(
    monthly_income: float,
    fixed_costs: float,
    variable_costs: float,
    debt_payments: float,
    savings_goal: float,
    priority: str,
) -> BudgetPlan:
    current_essentials = fixed_costs + (variable_costs * 0.45)
    current_lifestyle = variable_costs * 0.55

    savings_target_ratio = {
        "Aggressive saving": 0.28,
        "Balanced plan": 0.20,
        "Debt payoff": 0.16,
        "Low-stress budget": 0.12,
    }[priority]
    debt_target_ratio = {
        "Aggressive saving": 0.10,
        "Balanced plan": 0.10,
        "Debt payoff": 0.18,
        "Low-stress budget": 0.08,
    }[priority]

    recommended_savings = max(monthly_income * savings_target_ratio, savings_goal / 12 if savings_goal else 0)
    recommended_debt = max(debt_payments, monthly_income * debt_target_ratio)
    recommended_essentials = min(current_essentials, monthly_income * 0.55)

    total_allocated = recommended_essentials + current_lifestyle + recommended_savings + recommended_debt
    leftover = monthly_income - total_allocated

    if leftover < 0:
        current_lifestyle = max(0.0, current_lifestyle + leftover)
        leftover = monthly_income - (
            recommended_essentials + current_lifestyle + recommended_savings + recommended_debt
        )

    if leftover < 0:
        recommended_savings = max(0.0, recommended_savings + leftover)
        leftover = monthly_income - (
            recommended_essentials + current_lifestyle + recommended_savings + recommended_debt
        )

    emergency_months = 0.0
    if recommended_essentials > 0:
        emergency_months = (recommended_savings * 6) / recommended_essentials

    savings_rate = (recommended_savings / monthly_income) if monthly_income else 0.0

    return BudgetPlan(
        income=round(monthly_income, 2),
        essentials=round(recommended_essentials, 2),
        lifestyle=round(current_lifestyle, 2),
        savings=round(recommended_savings, 2),
        debt=round(recommended_debt, 2),
        leftover=round(leftover, 2),
        emergency_months=round(emergency_months, 1),
        savings_rate=round(savings_rate * 100, 1),
    )


def build_agent_response(plan: BudgetPlan, savings_goal: float, priority: str) -> str:
    lines = [
        f"I’d build your monthly plan around ${plan.essentials:,.0f} for essentials, "
        f"${plan.lifestyle:,.0f} for flexible spending, ${plan.savings:,.0f} for savings, "
        f"and ${plan.debt:,.0f} for debt payments.",
        f"That gives you a savings rate of {plan.savings_rate:.1f}% with about ${plan.leftover:,.0f} left as buffer.",
    ]

    if savings_goal > 0:
        months = savings_goal / plan.savings if plan.savings else 0
        lines.append(f"At this pace, a ${savings_goal:,.0f} goal would take about {months:.1f} months to reach.")

    if priority == "Debt payoff":
        lines.append("Because debt payoff is the priority, I’m steering extra cash toward repayment before lifestyle growth.")
    elif priority == "Aggressive saving":
        lines.append("Because saving is the priority, the plan leans intentionally conservative on discretionary spending.")
    elif priority == "Low-stress budget":
        lines.append("Because flexibility matters most here, the plan keeps more breathing room in your monthly spending.")

    if plan.leftover < 150:
        lines.append("Your buffer is thin, so trimming subscriptions, dining out, or impulse shopping would be the first move.")
    if plan.emergency_months < 3:
        lines.append("Your emergency-fund pace is still light, so building cash reserves should stay near the top of the plan.")

    return " ".join(lines)


def build_recommendations(plan: BudgetPlan, fixed_costs: float, variable_costs: float) -> list[str]:
    recommendations: list[str] = []

    fixed_ratio = fixed_costs / plan.income if plan.income else 0
    variable_ratio = variable_costs / plan.income if plan.income else 0

    if fixed_ratio > 0.35:
        recommendations.append("Fixed costs are heavy relative to income, so rent, insurance, and recurring bills are the highest-leverage review points.")
    if variable_ratio > 0.25:
        recommendations.append("Variable spending is elevated, so a weekly cap for dining, shopping, and entertainment would free up cash fast.")
    if plan.savings_rate >= 20:
        recommendations.append("Your savings rate is already strong; automate transfers right after payday so the plan happens consistently.")
    if plan.debt > 0:
        recommendations.append("Use the avalanche method for highest-interest balances, or the snowball method if quick wins keep you engaged.")
    if plan.leftover > 300:
        recommendations.append("You have extra monthly margin, so split the buffer between faster savings and a small guilt-free spending allowance.")

    if not recommendations:
        recommendations.append("This is already a balanced starting point. Focus on consistency, automation, and a monthly review rhythm.")

    return recommendations


def build_projection(plan: BudgetPlan, savings_goal: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cumulative_savings = 0.0
    cumulative_debt = 0.0
    for month in range(1, 13):
        cumulative_savings += plan.savings
        cumulative_debt += plan.debt
        progress = min(100.0, (cumulative_savings / savings_goal) * 100) if savings_goal > 0 else 0.0
        rows.append(
            {
                "Month": f"Month {month}",
                "Savings built": round(cumulative_savings, 2),
                "Debt paid": round(cumulative_debt, 2),
                "Goal progress %": round(progress, 1),
            }
        )
    return pd.DataFrame(rows)


def default_category_budget() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Category": "Housing", "Type": "Essential", "Planned": 1400.0},
            {"Category": "Utilities", "Type": "Essential", "Planned": 220.0},
            {"Category": "Groceries", "Type": "Essential", "Planned": 450.0},
            {"Category": "Transportation", "Type": "Essential", "Planned": 250.0},
            {"Category": "Insurance", "Type": "Essential", "Planned": 180.0},
            {"Category": "Dining Out", "Type": "Flexible", "Planned": 200.0},
            {"Category": "Entertainment", "Type": "Flexible", "Planned": 120.0},
            {"Category": "Shopping", "Type": "Flexible", "Planned": 180.0},
            {"Category": "Subscriptions", "Type": "Flexible", "Planned": 60.0},
            {"Category": "Travel", "Type": "Flexible", "Planned": 120.0},
        ]
    )


def parse_transactions_csv(file_obj: Any) -> pd.DataFrame:
    df = pd.read_csv(file_obj)
    if df.empty:
        raise ValueError("The uploaded CSV is empty.")

    normalized = {column: column.strip().lower().replace(" ", "_") for column in df.columns}
    df = df.rename(columns=normalized)

    amount_col = _find_column(df, ["amount", "transaction_amount", "debit", "value", "spent", "expense_amount"])
    category_col = _find_column(df, ["category", "merchant_category", "budget_category", "label"])
    date_col = _find_column(df, ["date", "transaction_date", "posted_date", "timestamp"])
    type_col = _find_column(df, ["type", "transaction_type", "direction"])

    if amount_col is None:
        raise ValueError("The CSV needs an amount-like column such as amount, debit, or transaction_amount.")

    working_df = df.copy()
    working_df["amount"] = pd.to_numeric(working_df[amount_col], errors="coerce")
    working_df = working_df.dropna(subset=["amount"])
    if working_df.empty:
        raise ValueError("No usable numeric amounts were found in the CSV.")

    if category_col is None:
        working_df["category"] = "Uncategorized"
    else:
        working_df["category"] = working_df[category_col].fillna("Uncategorized").astype(str).str.strip()
        working_df["category"] = working_df["category"].replace("", "Uncategorized")

    if date_col is not None:
        working_df["date"] = pd.to_datetime(working_df[date_col], errors="coerce")
    else:
        working_df["date"] = pd.NaT

    if type_col is not None:
        direction_series = working_df[type_col].astype(str).str.lower()
        income_mask = direction_series.str.contains("income|deposit|credit|salary|payroll|refund", regex=True)
        working_df = working_df.loc[~income_mask].copy()

    if working_df.empty:
        raise ValueError("The CSV only appeared to contain income transactions after filtering.")

    if (working_df["amount"] < 0).any() and (working_df["amount"] > 0).any():
        expense_mask = working_df["amount"] < 0
        working_df = working_df.loc[expense_mask].copy()
        working_df["amount"] = working_df["amount"].abs()
    else:
        working_df["amount"] = working_df["amount"].abs()

    return working_df[["date", "category", "amount"]].sort_values(by="amount", ascending=False)


def summarize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Category", "Actual", "Monthly estimate", "Share %"])

    grouped = df.groupby("category", as_index=False)["amount"].sum()
    grouped = grouped.rename(columns={"category": "Category", "amount": "Actual"})
    total = grouped["Actual"].sum()

    valid_dates = df["date"].dropna()
    month_count = 1
    if not valid_dates.empty:
        periods = valid_dates.dt.to_period("M")
        month_count = max(periods.nunique(), 1)

    grouped["Monthly estimate"] = grouped["Actual"] / month_count
    grouped["Share %"] = (grouped["Actual"] / total) * 100 if total else 0.0
    return grouped.sort_values(by="Actual", ascending=False).reset_index(drop=True)


def merge_category_targets(
    base_budget_df: pd.DataFrame,
    actuals_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    budget_df = base_budget_df.copy()
    if "Actual" not in budget_df.columns:
        budget_df["Actual"] = 0.0
    if "Variance" not in budget_df.columns:
        budget_df["Variance"] = 0.0

    if actuals_df is None or actuals_df.empty:
        budget_df["Actual"] = budget_df["Actual"].fillna(0.0)
        budget_df["Variance"] = budget_df["Planned"] - budget_df["Actual"]
        return budget_df

    merged = budget_df.merge(actuals_df[["Category", "Monthly estimate"]], on="Category", how="outer")
    merged["Type"] = merged["Type"].fillna("Flexible")
    merged["Planned"] = merged["Planned"].fillna(0.0)
    merged["Monthly estimate"] = merged["Monthly estimate"].fillna(0.0)
    merged["Actual"] = merged["Monthly estimate"]
    merged["Variance"] = merged["Planned"] - merged["Actual"]
    return merged.drop(columns=["Monthly estimate"]).sort_values(by=["Type", "Category"]).reset_index(drop=True)


def save_budget_snapshot(
    username: str,
    plan: BudgetPlan,
    fixed_costs: float,
    variable_costs: float,
    debt_payments: float,
    savings_goal: float,
    priority: str,
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = _read_history()
    history.append(
        {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "username": username,
            "priority": priority,
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "debt_payments": round(debt_payments, 2),
            "savings_goal": round(savings_goal, 2),
            **asdict(plan),
        }
    )
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")


def load_budget_history(username: str) -> pd.DataFrame:
    history = _read_history()
    if not history:
        return pd.DataFrame()
    history_df = pd.DataFrame(history)
    user_df = history_df.loc[history_df["username"] == username].copy()
    if user_df.empty:
        return pd.DataFrame()
    user_df["saved_at"] = pd.to_datetime(user_df["saved_at"], errors="coerce")
    return user_df.sort_values(by="saved_at")


def build_budget_context(
    plan: BudgetPlan,
    fixed_costs: float,
    variable_costs: float,
    debt_payments: float,
    savings_goal: float,
    priority: str,
    category_df: pd.DataFrame,
    history_df: pd.DataFrame,
) -> dict[str, Any]:
    category_records = []
    if not category_df.empty:
        category_records = (
            category_df[["Category", "Type", "Planned", "Actual", "Variance"]]
            .fillna(0.0)
            .to_dict(orient="records")
        )

    history_records = []
    if not history_df.empty:
        slim_history = history_df.tail(6).copy()
        slim_history["saved_at"] = slim_history["saved_at"].dt.strftime("%Y-%m-%d")
        history_records = slim_history[
            ["saved_at", "priority", "savings", "debt", "leftover", "savings_rate"]
        ].to_dict(orient="records")

    return {
        "budget_inputs": {
            "monthly_income": plan.income,
            "fixed_costs": fixed_costs,
            "variable_costs": variable_costs,
            "debt_payments": debt_payments,
            "savings_goal": savings_goal,
            "priority": priority,
        },
        "recommended_plan": asdict(plan),
        "category_breakdown": category_records,
        "history": history_records,
    }


def fallback_chat_reply(
    question: str,
    plan: BudgetPlan,
    recommendations: list[str],
    category_df: pd.DataFrame,
) -> str:
    prompt = question.lower()

    if "save" in prompt:
        return recommendations[0]
    if "debt" in prompt:
        return (
            "If your debt has high interest, prioritize paying more than the minimum while still keeping a small emergency cushion."
        )
    if "category" in prompt or "spending" in prompt:
        if category_df.empty:
            return "Upload a CSV or fill in category targets to see where spending is drifting versus plan."
        over_budget = category_df.loc[category_df["Variance"] < 0].sort_values(by="Variance")
        if over_budget.empty:
            return "Your categories are on or under plan right now. Keep watching flexible spending first."
        row = over_budget.iloc[0]
        return f"{row['Category']} is your most over-budget category right now, so that is the cleanest place to tighten spending."
    return (
        f"Your current plan targets {plan.savings_rate:.1f}% savings with a ${plan.leftover:,.0f} monthly buffer. "
        "Focus first on the biggest fixed cost or the most over-budget flexible category."
    )


def generate_openai_budget_reply(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    budget_context: dict[str, Any],
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The openai package is not installed. Add it to your environment first.") from exc

    client = OpenAI(api_key=api_key)
    developer_prompt = (
        "You are a practical budget planning assistant inside a Streamlit app. "
        "Use the provided budget context to answer the user's question. "
        "Be specific, supportive, and concise. Suggest concrete next actions. "
        "Do not claim to be a licensed financial advisor. "
        f"Budget context: {json.dumps(budget_context, default=str)}"
    )

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": developer_prompt}],
            },
            *[
                {
                    "role": message["role"],
                    "content": [{"type": "input_text", "text": message["content"]}],
                }
                for message in messages[-8:]
            ],
        ],
    )

    output_text = getattr(response, "output_text", "")
    if output_text:
        return output_text.strip()

    parts: list[str] = []
    for item in getattr(response, "output", []):
        if getattr(item, "type", None) != "message":
            continue
        for content in getattr(item, "content", []):
            if getattr(content, "type", None) in {"output_text", "text"}:
                text_value = getattr(content, "text", "")
                if isinstance(text_value, str):
                    parts.append(text_value)
                else:
                    value = getattr(text_value, "value", "")
                    if value:
                        parts.append(value)

    if not parts:
        raise RuntimeError("The OpenAI response did not include any text output.")
    return "\n".join(parts).strip()


def _read_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None
