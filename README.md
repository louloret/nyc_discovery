# NYC Discovery

A collection of scripts to discover and aggregate upcoming events in NYC from various sources.

## Scripts

- **scraper.py**: Scrapes events from blogs, newsletters, and websites.
- **find_reddit_cultural_events.py**: Searches Reddit for cultural events in NYC.
- **combine_summaries.py**: Combines the latest outputs from the scraper and Reddit finder into a single markdown summary.
- **email_combined_summary.py**: Emails the latest combined markdown summary as an attachment.
- **run_full_workflow.py**: Automates the entire workflow by running all scripts in sequence.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in a `.env` file:
   ```
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=your_reddit_user_agent
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   TO_ADDRESS=recipient_email@gmail.com
   ```

   For Gmail, you'll need an [App Password](https://support.google.com/accounts/answer/185833) if 2FA is enabled.

## Usage

- **Run the full workflow**:
  ```bash
  python run_full_workflow.py
  ```

- **Run individual scripts**:
  ```bash
  python scraper.py
  python find_reddit_cultural_events.py
  python combine_summaries.py
  python email_combined_summary.py
  ```

## Output

- **JSON files**: Raw event data from each source.
- **Markdown files**: Summaries of events, combined and emailed.

## Notes

- The workflow stops if any script fails.
- The latest combined markdown file is emailed as an attachment. 