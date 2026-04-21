from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PortfolioProject:
    name: str
    headline: str
    business_impact: str
    stack: List[str]
    highlights: List[str]


@dataclass(frozen=True)
class SkillArea:
    name: str
    level: int
    summary: str
    tools: List[str]


PROFILE = {
    "name": "Ashwini Balasubramanian",
    "title": "Data Science | AI | Machine Learning",
    "pitch": (
        "I build data products that connect analytics, ML modeling, and business "
        "decision-making. My sweet spot is turning messy data into clear insight, "
        "deployable models, and stakeholder-friendly storytelling."
    ),
    "strengths": [
        "End-to-end ML workflow design",
        "Predictive modeling and evaluation",
        "LLM and AI product prototyping",
        "Experimentation, analytics, and storytelling",
    ],
}


SKILLS: List[SkillArea] = [
    SkillArea(
        name="Machine Learning",
        level=92,
        summary="Builds supervised learning pipelines, compares models, and explains tradeoffs clearly.",
        tools=["scikit-learn", "XGBoost", "Feature engineering", "Cross-validation"],
    ),
    SkillArea(
        name="Data Science",
        level=95,
        summary="Moves from raw data to business insight with strong EDA, KPI design, and communication.",
        tools=["Python", "Pandas", "SQL", "Visualization", "A/B testing"],
    ),
    SkillArea(
        name="AI Product Thinking",
        level=88,
        summary="Frames AI solutions around user problems, reliability, and measurable business value.",
        tools=["Prompt design", "Evaluation frameworks", "Retrieval patterns", "Human-in-the-loop flows"],
    ),
    SkillArea(
        name="MLOps & Deployment",
        level=81,
        summary="Thinks beyond notebooks by planning reproducibility, monitoring, and production handoffs.",
        tools=["Model packaging", "APIs", "Experiment tracking", "Monitoring metrics"],
    ),
]


PROJECTS: List[PortfolioProject] = [
    PortfolioProject(
        name="Customer Churn Intelligence",
        headline="Built a classification pipeline to flag customers at retention risk.",
        business_impact="Enabled teams to prioritize outreach using ranked churn risk segments.",
        stack=["Python", "Pandas", "scikit-learn", "SHAP", "SQL"],
        highlights=[
            "Designed feature engineering around product usage, tenure, and support interactions.",
            "Benchmarked logistic regression, random forest, and gradient boosting models.",
            "Translated feature importance into stakeholder actions for marketing and CX teams.",
        ],
    ),
    PortfolioProject(
        name="Demand Forecasting Assistant",
        headline="Created a forecasting workflow for planning inventory and staffing demand.",
        business_impact="Improved planning conversations by exposing trend, seasonality, and uncertainty bands.",
        stack=["Python", "Time series", "Prophet", "Plotly", "Scenario analysis"],
        highlights=[
            "Compared statistical and ML-driven forecasting approaches.",
            "Built scenario toggles to communicate best-case and worst-case planning ranges.",
            "Packaged forecasts into dashboard-friendly outputs for non-technical teams.",
        ],
    ),
    PortfolioProject(
        name="LLM Knowledge Support Agent",
        headline="Prototyped an AI assistant that answers domain-specific questions with grounded responses.",
        business_impact="Reduced search friction and demonstrated how AI can support internal workflows.",
        stack=["LLM workflows", "Prompt engineering", "Retrieval design", "Evaluation rubrics"],
        highlights=[
            "Structured retrieval-first response patterns to reduce hallucinations.",
            "Defined evaluation criteria around accuracy, helpfulness, and trust.",
            "Focused on product usability, fallback behavior, and answer transparency.",
        ],
    ),
]


CASE_STUDY = {
    "dataset_rows": 128_450,
    "features": 37,
    "baseline_auc": 0.74,
    "production_auc": 0.89,
    "lift": 20.3,
    "retention_gain": 11.8,
}


CHAT_PLAYBOOK: Dict[str, str] = {
    "introduce": (
        "I’m an AI/Data Science portfolio agent representing Ashwini Balasubramanian. "
        "I can walk through ML projects, explain modeling choices, discuss business impact, "
        "and summarize strengths across analytics, AI, and deployment."
    ),
    "skills": (
        "Ashwini’s profile is strongest where analytics and applied ML meet product thinking: "
        "data wrangling, exploratory analysis, supervised learning, model evaluation, experimentation, "
        "and communicating the 'why' behind results. There is also a strong emerging AI layer with "
        "prompt design, retrieval-based assistant patterns, and evaluation-minded AI workflows."
    ),
    "projects": (
        "Three showcase themes stand out: churn prediction, demand forecasting, and a knowledge-support AI agent. "
        "Together they show predictive modeling, time-series reasoning, and applied AI product design."
    ),
    "deployment": (
        "A strong deployment story here is not just 'I trained a model' but 'I designed a repeatable workflow.' "
        "That includes feature pipelines, versioned experiments, API or dashboard delivery, monitoring drift, "
        "and defining the business metric the model is responsible for improving."
    ),
    "leadership": (
        "A recruiter-friendly strength is the ability to connect technical work to decisions. "
        "That means framing problems clearly, prioritizing metrics that matter, and translating model outputs "
        "into actions that operations, product, or business teams can actually use."
    ),
    "default": (
        "I can help with questions about ML projects, DS skills, model choices, AI workflows, deployment, "
        "or how this profile fits roles in analytics, applied AI, and machine learning."
    ),
}


def classify_prompt(user_prompt: str) -> str:
    prompt = user_prompt.lower()

    keyword_map = {
        "introduce": ["who are you", "introduce", "about", "profile"],
        "skills": ["skill", "strength", "tools", "technology", "stack"],
        "projects": ["project", "portfolio", "work", "case study"],
        "deployment": ["deploy", "production", "mlops", "monitor", "api"],
        "leadership": ["leadership", "stakeholder", "communication", "business", "impact"],
    }

    for intent, keywords in keyword_map.items():
        if any(keyword in prompt for keyword in keywords):
            return intent
    return "default"


def answer_prompt(user_prompt: str) -> str:
    intent = classify_prompt(user_prompt)
    response = CHAT_PLAYBOOK[intent]

    if "churn" in user_prompt.lower():
        response += (
            " For churn work specifically, Ashwini emphasizes feature engineering, class balance, "
            "model comparison, and explaining retention levers rather than just reporting AUC."
        )
    if "forecast" in user_prompt.lower():
        response += (
            " For forecasting, the portfolio focuses on seasonality, scenario planning, and presenting "
            "uncertainty clearly so the output supports real business planning."
        )
    if "llm" in user_prompt.lower() or "agent" in user_prompt.lower():
        response += (
            " On the AI side, the story centers on retrieval-aware design, prompt quality, safe fallbacks, "
            "and lightweight evaluation so an assistant is useful and trustworthy."
        )
    return response


def recruiter_pitch() -> str:
    return (
        f"{PROFILE['name']} is an applied data scientist with a portfolio that blends classic ML, "
        "analytics, and modern AI prototyping. The differentiator is an ability to move from raw data "
        "to model insight to business narrative without losing rigor."
    )


def project_cards() -> List[Dict[str, str]]:
    cards = []
    for project in PROJECTS:
        cards.append(
            {
                "name": project.name,
                "headline": project.headline,
                "impact": project.business_impact,
                "stack": " | ".join(project.stack),
                "highlights": "\n".join(f"- {item}" for item in project.highlights),
            }
        )
    return cards
