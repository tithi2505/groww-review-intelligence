# Groww Review Intelligence

**Review-analysis and approval-gated automation prototype** built with Streamlit, Python, and Make.com.

**[Open the working Streamlit prototype](https://groww-review-intelligence-apqm3eq4uafrls6hbbmivl.streamlit.app/)**

## Project overview

This prototype turns a bundled dataset of public Groww app reviews into structured product insights and a reusable, source-grounded explanation of trading fees. A human reviews the outputs before triggering any connected workflow.

The project combines **review analysis** with **workflow automation**: after approval, Make.com appends the analysis to a Google Doc and creates a Gmail draft for review. **It does not send emails automatically.**

## Features

- **Review intelligence:** Analyse the included reviews, identify the top three recurring themes, show review counts and selected user quotes, and flag recurring fee-related concerns.
- **Weekly Product Pulse:** Generate a concise summary of review themes, customer pain points, and suggested product actions; download it as Markdown.
- **Customer Fee Explainer:** Retrieve relevant facts from the included source-context dataset using TF-IDF similarity and present clarification points alongside official Groww pricing and MTF links.
- **Human approval gate:** Require an explicit checkbox and **Approve & Log Outputs** click before the external workflow is triggered.
- **Connected actions:** Append a review-intelligence entry to Google Docs and create a Gmail draft with a subject and body through Make.com.
- **Demo mode:** If no Make webhook is configured, prepare local sample outputs instead of triggering external services.

## End-to-end workflow

```text
Bundled public review dataset (reviews.csv)
                 |
                 v
        Streamlit analysis app
     - Themes, counts and quotes
     - Weekly Product Pulse
     - Fee explanation + sources
                 |
                 v
        Human review and approval
                 |
                 v
          Make.com webhook
                 |
                 v
       +-----------------------+
       |                       |
       v                       v
Google Docs: append       Gmail: create a
analysis entry            draft (do not send)
```

### Make.com scenario

The connected Make.com scenario contains three modules:

1. **Webhooks — Custom webhook:** Receives the approved JSON payload from the Streamlit app.
2. **Google Docs — Insert a Paragraph to a Document:** Appends the date, theme names, product pulse, identified fee issue, customer explanation and source links to the internal **Groww Review Intelligence Log**.
3. **Gmail — Create a draft email:** Uses the payload's `email_subject` and `email_body` fields to create a draft for manual review.

The Make.com scenario and the connected Google Doc/Gmail account are configured outside this repository; their private contents and credentials are not included in the source code.

## Technology

- **Python, Streamlit:** User interface and approval flow
- **Pandas:** Review-data processing
- **scikit-learn:** TF-IDF retrieval and cosine similarity for fee-source context
- **Requests:** HTTP POST to the Make.com webhook
- **Make.com:** No-code automation connecting Google Docs and Gmail

**Implementation note:** Theme detection is keyword/rule-based and the fee-context retrieval uses TF-IDF. The repository does not call a generative AI model or a live reviews API. The analysis uses the dataset committed to this repository, so its results do not automatically update with new reviews.

## Repository files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit UI, review insights, approval and workflow trigger |
| `analysis.py` | Review classification, recurring-issue detection and product-pulse generation |
| `mcp_actions.py` | Approval payload, email-draft construction, sample outputs and Make webhook call |
| `reviews.csv` | Included review dataset |
| `source_context.csv` | Fee-related factual context and source-check dates |
| `sources.csv` | Source reference data |
| `requirements.txt` | Python dependencies |

## Run locally

1. Clone the repository.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the app:

   ```bash
   streamlit run app.py
   ```

To enable the Make.com integration, configure `MAKE_WEBHOOK_URL` as a **Streamlit secret** in your deployment (or in a local `.streamlit/secrets.toml` file that is **not committed to GitHub**). Without this secret, the app uses demo mode and prepares local Markdown outputs.

## How to demonstrate

1. Open the [live prototype](https://groww-review-intelligence-apqm3eq4uafrls6hbbmivl.streamlit.app/).
2. Review the top themes, real user quotes, Weekly Product Pulse and Customer Fee Explainer.
3. Tick the approval checkbox and select **Approve & Log Outputs**.
4. Expand **View Email Draft** and **View Notes / Doc Entry** to inspect the generated content.
5. With the Make webhook configured, the approved payload also creates a new entry in the owner's Google Doc and a new Gmail draft.

**Demo caution:** Approval in a connected public deployment triggers real actions in the owner's Google Docs and Gmail account. Repeated approvals create additional entries and drafts. The connected documents and drafts are private and are not visible to public visitors.

## Scope and disclaimer

This is an educational prototype using a fixed review dataset and official-source context for fee clarification. It is **not affiliated with Groww**, does not execute trades, does not provide investment advice, and never automatically sends customer emails.
