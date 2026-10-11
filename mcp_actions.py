import json
from pathlib import Path
from datetime import datetime

import requests


OUTPUT_DIR = Path("sample_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

NOTES_FILE = OUTPUT_DIR / "notes_entry.md"
EMAIL_FILE = OUTPUT_DIR / "email_draft.md"


def build_action_payload(
    top_themes,
    weekly_pulse,
    identified_fee_issue,
    explanation_bullets,
    source_links
):
    """
    Structured payload used for the approval-gated actions.
    """

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "top_themes": top_themes,
        "weekly_pulse": weekly_pulse,
        "identified_fee_issue": identified_fee_issue,
        "explanation_bullets": explanation_bullets,
        "source_links": source_links
    }


def build_email_draft(
    weekly_pulse,
    identified_fee_issue,
    explanation_bullets,
    source_links
):
    subject = (
        "Weekly Product Pulse + Customer Clarification — "
        f"{identified_fee_issue}"
    )

    bullets_text = "\n".join(
        f"- {bullet}"
        for bullet in explanation_bullets
    )

    sources_text = "\n".join(
        f"- {link}"
        for link in source_links
    )

    body = f"""
Hi team,

Sharing this week's product pulse and a reusable customer clarification based on recurring feedback.

WEEKLY PRODUCT PULSE

{weekly_pulse}

CUSTOMER CLARIFICATION

Issue:
{identified_fee_issue}

{bullets_text}

Official sources:
{sources_text}

This explanation is facts-only and should not be treated as investment advice.

Regards,
Product Team
""".strip()

    return {
        "subject": subject,
        "body": body
    }


def save_notes_entry(payload):
    """
    Demo-mode equivalent of appending the structured output
    to an internal Notes/Doc tool.
    """

    themes = "\n".join(
        f"- {theme['theme']} ({theme['count']} reviews)"
        for theme in payload["top_themes"]
    )

    bullets = "\n".join(
        f"- {bullet}"
        for bullet in payload["explanation_bullets"]
    )

    sources = "\n".join(
        f"- {link}"
        for link in payload["source_links"]
    )

    content = f"""# Review Intelligence Entry

**Date:** {payload["date"]}

## Top Themes

{themes}

## Weekly Product Pulse

{payload["weekly_pulse"]}

## Identified Fee Issue

{payload["identified_fee_issue"]}

## Customer Explanation

{bullets}

## Official Sources

{sources}
"""

    NOTES_FILE.write_text(
        content,
        encoding="utf-8"
    )

    return str(NOTES_FILE)


def save_email_draft(email):
    """
    Demo-mode equivalent of creating a Gmail draft.
    This function never sends the email.
    """

    content = f"""# Email Draft

**Subject:** {email["subject"]}

## Body

{email["body"]}
"""

    EMAIL_FILE.write_text(
        content,
        encoding="utf-8"
    )

    return str(EMAIL_FILE)


def send_to_make_webhook(
    webhook_url,
    payload,
    email
):
    """
    Optional real integration.

    A Make webhook can receive this payload and then:
    1. Append the note to Google Docs / Notion
    2. Create a Gmail draft

    It must NOT auto-send the email.
    """

    webhook_payload = {
    "action": "approved_product_review_update",
    "notes_entry": payload,
    "email_draft": email,
    "email_subject": email["subject"],
    "email_body": email["body"]
}

    response = requests.post(
        webhook_url,
        json=webhook_payload,
        timeout=20
    )

    response.raise_for_status()

    return {
        "status_code": response.status_code,
        "response": response.text
    }


def execute_approved_actions(
    payload,
    webhook_url=None
):
    """
    This function should ONLY be called after
    explicit user approval in the UI.
    """

    email = build_email_draft(
        weekly_pulse=payload["weekly_pulse"],
        identified_fee_issue=payload["identified_fee_issue"],
        explanation_bullets=payload["explanation_bullets"],
        source_links=payload["source_links"]
    )

    notes_path = save_notes_entry(payload)
    email_path = save_email_draft(email)

    result = {
        "approved": True,
        "notes_saved": True,
        "notes_path": notes_path,
        "email_draft_created": True,
        "email_path": email_path,
        "email_sent": False,
        "external_actions": False
    }

    if webhook_url:
        webhook_result = send_to_make_webhook(
            webhook_url,
            payload,
            email
        )

        result["external_actions"] = True
        result["webhook_result"] = webhook_result

    return result


if __name__ == "__main__":
    print(
        "MCP action layer ready. "
        "No action is executed without approval."
    )
