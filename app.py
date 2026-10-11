import streamlit as st
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from analysis import run_analysis
from mcp_actions import (
    build_action_payload,
    build_email_draft,
    execute_approved_actions
)


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Groww Review Intelligence",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# LOAD OFFICIAL SOURCE CONTEXT
# --------------------------------------------------

@st.cache_data
def load_source_context():
    df = pd.read_csv("source_context.csv")

    df["search_text"] = (
        df["topic"].astype(str)
        + " "
        + df["fact"].astype(str)
    )

    return df


source_context = load_source_context()


# --------------------------------------------------
# RETRIEVE OFFICIAL FEE CONTEXT
# --------------------------------------------------

def retrieve_fee_context(issue, top_k=9):

    documents = source_context["search_text"].tolist()

    query = (
        f"{issue} brokerage trading fees charges "
        "multiple orders statutory charges MTF interest pledge"
    )

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(
        documents + [query]
    )

    similarities = cosine_similarity(
        vectors[-1],
        vectors[:-1]
    ).flatten()

    ranked_indices = (
        similarities.argsort()[::-1][:top_k]
    )

    return source_context.iloc[
        ranked_indices
    ].copy()


# --------------------------------------------------
# BUILD GROUNDED FEE EXPLAINER
# --------------------------------------------------

def build_fee_explainer(issue):

    retrieved = retrieve_fee_context(issue)

    preferred_topics = [
        "Equity brokerage",
        "Multiple orders",
        "Additional trading charges",
        "MTF brokerage",
        "MTF interest",
        "MTF pledge charge"
    ]

    bullets = []

    for topic in preferred_topics:

        match = retrieved[
            retrieved["topic"] == topic
        ]

        if not match.empty:
            fact = match.iloc[0]["fact"]

            if fact not in bullets:
                bullets.append(fact)

    # Maximum 6 bullets as required
    bullets = bullets[:6]

    # Two official sources
    source_links = [
        "https://groww.in/pricing",
        "https://groww.in/stocks/mtf"
    ]

    checked_dates = pd.to_datetime(
        source_context["last_checked"],
        errors="coerce"
    )

    latest_checked = checked_dates.max()

    if pd.isna(latest_checked):
        last_checked = "Not available"
    else:
        last_checked = latest_checked.strftime(
            "%d %B %Y"
        )

    return {
        "bullets": bullets,
        "source_links": source_links,
        "last_checked": last_checked
    }


# --------------------------------------------------
# OPTIONAL MAKE WEBHOOK
# --------------------------------------------------

def get_make_webhook_url():

    try:
        return st.secrets.get(
            "MAKE_WEBHOOK_URL",
            ""
        )
    except Exception:
        return ""


# --------------------------------------------------
# RUN REVIEW ANALYSIS
# --------------------------------------------------

analysis = run_analysis(
    write_pulse=False
)

fee_explainer = build_fee_explainer(
    analysis["identified_fee_issue"]
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("Groww Review Intelligence")

st.write(
    "AI-assisted workflow that turns recent public "
    "customer reviews into product insights and "
    "support-ready communication."
)

st.caption(
    "Public review data only • Official Groww sources "
    "used for fee clarification"
)

st.divider()


# --------------------------------------------------
# DATASET OVERVIEW
# --------------------------------------------------

st.subheader("1. Review Intelligence")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Reviews analysed",
        analysis["reviews_analyzed"]
    )

with col2:
    st.metric(
        "Themes identified",
        len(analysis["theme_counts"])
    )

with col3:
    st.metric(
        "Fee-related reviews",
        analysis["fee_review_count"]
    )


# --------------------------------------------------
# TOP THEMES
# --------------------------------------------------

st.markdown("### Top 3 Themes")

theme_columns = st.columns(3)

for index, item in enumerate(
    analysis["top_themes"]
):

    with theme_columns[index]:

        st.markdown(
            f"**{index + 1}. "
            f"{item['theme']}**"
        )

        st.write(
            f"{item['count']} reviews"
        )


# --------------------------------------------------
# REAL USER QUOTES
# --------------------------------------------------

st.markdown("### Real User Quotes")

for quote in analysis["quotes"]:

    st.info(
        f'"{quote}"'
    )


# --------------------------------------------------
# FEE ISSUE
# --------------------------------------------------

st.markdown(
    "### Recurring Fee / Charge Issue"
)

st.warning(
    analysis["identified_fee_issue"]
)

st.write(
    "Lower-rated reviews repeatedly mention "
    "brokerage, MTF costs, charges or unclear "
    "trading fees. The clarification below uses "
    "official Groww sources rather than review claims."
)

st.divider()


# --------------------------------------------------
# WEEKLY PRODUCT PULSE
# --------------------------------------------------

st.subheader(
    "2. Weekly Product Pulse"
)

st.markdown(
    analysis["weekly_pulse"]
)

pulse_word_count = len(
    analysis["weekly_pulse"].split()
)

st.caption(
    f"Word count: {pulse_word_count} "
    "(maximum allowed: 250)"
)

st.download_button(
    label="Download Weekly Product Pulse",
    data=analysis["weekly_pulse"],
    file_name="weekly_product_pulse.md",
    mime="text/markdown"
)

st.divider()


# --------------------------------------------------
# FEE EXPLAINER
# --------------------------------------------------

st.subheader(
    "3. Customer Fee Explainer"
)

st.markdown(
    f"**Issue identified from reviews:** "
    f"{analysis['identified_fee_issue']}"
)

for bullet in fee_explainer["bullets"]:
    st.markdown(
        f"- {bullet}"
    )

st.markdown("**Official sources:**")

for link in fee_explainer["source_links"]:
    st.markdown(
        f"- {link}"
    )

st.caption(
    f"Last checked: "
    f"{fee_explainer['last_checked']}"
)

st.info(
    "Facts-only clarification. "
    "This is not investment advice."
)

st.divider()


# --------------------------------------------------
# APPROVAL GATE
# --------------------------------------------------

st.subheader(
    "4. Approval & Internal Actions"
)

st.write(
    "The product pulse and fee explanation are ready. "
    "No external action will happen until approval."
)

st.warning(
    "No document has been updated and no email "
    "has been created or sent yet."
)

approved = st.checkbox(
    "I reviewed the outputs and approve logging "
    "them to internal tools."
)


# --------------------------------------------------
# BUILD PAYLOAD
# --------------------------------------------------

payload = build_action_payload(
    top_themes=analysis["top_themes"],
    weekly_pulse=analysis["weekly_pulse"],
    identified_fee_issue=(
        analysis["identified_fee_issue"]
    ),
    explanation_bullets=(
        fee_explainer["bullets"]
    ),
    source_links=(
        fee_explainer["source_links"]
    )
)


# --------------------------------------------------
# EXECUTE ONLY AFTER APPROVAL
# --------------------------------------------------

if st.button(
    "Approve & Log Outputs",
    disabled=not approved,
    type="primary"
):

    webhook_url = get_make_webhook_url()

    try:

        result = execute_approved_actions(
            payload=payload,
            webhook_url=(
                webhook_url
                if webhook_url
                else None
            )
        )

        st.session_state[
            "action_result"
        ] = result

        st.session_state[
            "approved_payload"
        ] = payload

        st.success(
            "Approval received."
        )

    except Exception as error:

        st.error(
            f"Action failed: {error}"
        )


# --------------------------------------------------
# POST-APPROVAL STATUS
# --------------------------------------------------

if "action_result" in st.session_state:

    result = st.session_state[
        "action_result"
    ]

    st.markdown(
        "### Action Status"
    )

    st.success(
        "✓ Internal Notes/Doc entry prepared"
    )

    st.success(
        "✓ Email draft prepared"
    )

    st.info(
        "Email was NOT sent."
    )

    if result.get(
        "external_actions"
    ):

        st.success(
            "✓ Approved payload sent to "
            "the connected Make workflow"
        )

    else:

        st.warning(
            "Demo mode: outputs were created "
            "inside the prototype. Connect the "
            "Make webhook to append to Google Docs "
            "and create the Gmail draft."
        )


    # ----------------------------------------------
    # EMAIL DRAFT PREVIEW
    # ----------------------------------------------

    email = build_email_draft(
        weekly_pulse=analysis[
            "weekly_pulse"
        ],
        identified_fee_issue=analysis[
            "identified_fee_issue"
        ],
        explanation_bullets=fee_explainer[
            "bullets"
        ],
        source_links=fee_explainer[
            "source_links"
        ]
    )

    with st.expander(
        "View Email Draft"
    ):

        st.markdown(
            f"**Subject:** "
            f"{email['subject']}"
        )

        st.text(
            email["body"]
        )


    # ----------------------------------------------
    # NOTES PAYLOAD PREVIEW
    # ----------------------------------------------

    with st.expander(
        "View Notes / Doc Entry"
    ):

        st.json(
            payload
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Groww Review Intelligence prototype • "
    "Reviews are public Google Play feedback • "
    "Fee explanations are grounded in official "
    "Groww pricing and MTF documentation."
)
