"""Project identity and draft roster for the capstone UI.

Names are transcribed from "Capstone Team Plan.xlsx", sheet
"3. Team & strengths". Roles and individual contributions are omitted
because the workbook marks them as proposed, not confirmed.
"""

PROJECT_NAME = "InvestigateIQ"
PROJECT_DESCRIPTION = "AI-assisted AML case investigation copilot"
PROJECT_SLOGAN = "Trace the evidence. Own the decision."
GROUP_LABEL = "Capstone Group 7"
COURSE_LABEL = "Leadership with AI, IIT Bombay"

TEAM_MEMBERS = (
    "Rahul Chainani",
    "Lakshmi",
    "Laxman Singh",
    "Pankaj",
    "RS",
    "Sweta Singh",
)

TEAM_RESPONSIBILITIES = {
    "Rahul Chainani": (
        "Application development & integration",
        "Review the Python/Streamlit app and SQLite data flow; keep the code, tests, and deployment path working together.",
    ),
    "Lakshmi": (
        "Requirements & case-study mapping",
        "Check the user needs and acceptance criteria; connect the suspicious and legitimate comparison cases to course case studies.",
    ),
    "Laxman Singh": (
        "User experience & product walkthrough",
        "Check each screen's purpose, flow, tooltips, readability, and projector-friendly presentation.",
    ),
    "Pankaj": (
        "AI workflow & evidence review",
        "Explain the six investigation steps and retrieval approach; check that draft findings point back to evidence.",
    ),
    "RS": (
        "Quality assurance & edge cases",
        "Run the fictional case scenarios, cached fallback, and missing or conflicting evidence checks; log reproducible issues.",
    ),
    "Sweta Singh": (
        "Course linkage & project explanation",
        "Map taught concepts to the working screens and prepare a simple explanation of design choices and limitations.",
    ),
}

ROSTER_NOTE = (
    "Draft roster and proposed responsibility areas for team discussion. "
    "These are not claims about work already completed by each person. "
    "Please confirm membership, full names, group name, and assignments before final submission."
)
