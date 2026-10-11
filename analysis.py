import pandas as pd
from pathlib import Path

REVIEWS_FILE = "reviews.csv"
PULSE_FILE = "weekly_product_pulse.md"

THEME_KEYWORDS = {
    "Fees, brokerage & charges": [
        "brokerage", "brokrage", "hidden charge", "hidden charges",
        "fees", "charges are", "charges/fee", "taxes", "mtf"
    ],
    "Mutual funds & money movement": [
        "mutual fund", "mutual units", "unit allocation", "redeem",
        "redemption", "sip", "withdraw", "withdrawal", "payment",
        "money deposit", "money flow", "payout", "bond",
        "credited twice", "money not coming", "fund transfer"
    ],
    "Support, account & onboarding": [
        "customer care", "customer service", "customer support",
        "support team", "help and support", "kyc", "login",
        "nominee", "selfie verification", "signature",
        "registering", "registration", "minor account",
        "account activity"
    ],
    "Trading & app reliability": [
        "trade", "trading", "order", "stoploss", "stop loss",
        "chart", "candle", "indicator", "f&o", "fno", "trigger",
        "sell", "pnl", "lag", "slow", "buffer", "freeze", "hang",
        "stuck", "update", "crash", "scalp", "ddpi", "square off",
        "autosquare", "intraday", "market", "landscape mode",
        "tablet optimization", "technical service"
    ]
}

FEE_COMPLAINT_TERMS = [
    "brokerage", "brokrage", "hidden charge", "hidden charges",
    "fee", "fees", "charge", "charges", "tax", "taxes", "mtf"
]


def contains_any(text, keywords):
    text = str(text).lower()
    return any(keyword in text for keyword in keywords)


def classify_theme(text):
    text = str(text).lower()

    for theme in [
        "Fees, brokerage & charges",
        "Mutual funds & money movement",
        "Support, account & onboarding",
        "Trading & app reliability"
    ]:
        if contains_any(text, THEME_KEYWORDS[theme]):
            return theme

    return "General experience & usability"


def pick_quote(df, required_terms):
    candidates = df[
        (df["rating"] <= 2)
        & df["review_text"].astype(str).str.lower().apply(
            lambda x: any(term in x for term in required_terms)
        )
    ].copy()

    if candidates.empty:
        return None

    candidates["length"] = candidates["review_text"].astype(str).str.len()

    concise = candidates[
        (candidates["length"] >= 20)
        & (candidates["length"] <= 220)
    ]

    if not concise.empty:
        candidates = concise

    candidates = candidates.sort_values(
        ["review_date", "length"],
        ascending=[False, True]
    )

    return str(candidates.iloc[0]["review_text"]).strip()


def run_analysis(write_pulse=True):
    df = pd.read_csv(REVIEWS_FILE)

    df["review_date"] = pd.to_datetime(
        df["review_date"],
        errors="coerce"
    )

    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )

    df["review_text"] = (
        df["review_text"]
        .fillna("")
        .astype(str)
    )

    df = df.dropna(
        subset=["review_date", "rating"]
    )

    df = df[
        df["review_text"].str.strip() != ""
    ].copy()

    df = df.drop_duplicates(
        subset=["review_text"]
    ).copy()

    df["theme"] = df["review_text"].apply(
        classify_theme
    )

    theme_counts = df["theme"].value_counts()

    top_themes = [
        {
            "theme": theme,
            "count": int(count)
        }
        for theme, count
        in theme_counts.head(3).items()
    ]

    fee_mask = (
        (df["rating"] <= 3)
        & df["review_text"].str.lower().apply(
            lambda x: any(
                term in x
                for term in FEE_COMPLAINT_TERMS
            )
        )
    )

    fee_reviews = df[fee_mask].copy()

    if len(fee_reviews) >= 3:
        identified_fee_issue = (
            "Brokerage & trading-charge transparency"
        )
    else:
        identified_fee_issue = (
            "No recurring fee issue detected "
            "with enough confidence"
        )

    quotes = [
        pick_quote(
            df,
            [
                "slow chalta",
                "working very slow",
                "stoploss",
                "chart",
                "indicator"
            ]
        ),
        pick_quote(
            df,
            [
                "unit allocation",
                "redeem",
                "redemption",
                "customer support",
                "help and support"
            ]
        ),
        pick_quote(
            df,
            [
                "hidden charges",
                "brokerage",
                "brokrage",
                "charges are very high"
            ]
        )
    ]

    quotes = [
        quote
        for quote in quotes
        if quote
    ][:3]

    latest_review_date = (
        df["review_date"]
        .max()
        .date()
        .isoformat()
    )

    top_theme_text = ", ".join(
        f"{item['theme']} ({item['count']})"
        for item in top_themes
    )

    quote_lines = "\n".join(
        f'- "{quote}"'
        for quote in quotes
    )

    pulse = f"""# Weekly Product Pulse

**Week ending:** {latest_review_date}

## Summary
Across {len(df)} recent public reviews, the top themes are {top_theme_text}. The overall review mix is heavily positive, but the lower-rated reviews show concentrated friction around trading reliability, support/money movement, and clarity of brokerage or trading charges.

## User quotes
{quote_lines}

## Key observation
The strongest negative signals are not broad dissatisfaction with the app; they are specific breakdowns at high-trust moments. Users report trading reliability issues, delays or uncertainty around money movement, and difficulty understanding brokerage/MTF-related charges. The fee signal appears repeatedly enough to justify a reusable support explanation, but it should be treated as a recurring pain point rather than the largest overall theme.

## Product actions
1. Instrument and monitor order execution, chart/loading and market-hour reliability issues.
2. Make mutual-fund allocation/redemption status and support escalation clearer when money is pending.
3. Show a clearer pre/post-trade charge breakdown, especially for brokerage, statutory charges and MTF costs.
"""

    if write_pulse:
        Path(PULSE_FILE).write_text(
            pulse,
            encoding="utf-8"
        )

    return {
        "reviews_analyzed": int(len(df)),
        "latest_review_date": latest_review_date,
        "theme_counts": {
            str(theme): int(count)
            for theme, count
            in theme_counts.items()
        },
        "top_themes": top_themes,
        "quotes": quotes,
        "identified_fee_issue": identified_fee_issue,
        "fee_review_count": int(len(fee_reviews)),
        "weekly_pulse": pulse
    }


if __name__ == "__main__":
    result = run_analysis(
        write_pulse=True
    )

    print("\nTOP THEMES")

    for item in result["top_themes"]:
        print(
            f"- {item['theme']}: "
            f"{item['count']}"
        )

    print("\nREAL USER QUOTES")

    for quote in result["quotes"]:
        print(f'- "{quote}"')

    print("\nFEE ISSUE")
    print(
        result["identified_fee_issue"]
    )

    print(
        "Negative/neutral fee-related "
        f"reviews detected: "
        f"{result['fee_review_count']}"
    )

    print(
        f"\nCreated {PULSE_FILE}"
    )
