# NYC Discovery Agent

A smart agent that discovers and curates unique NYC experiences by analyzing various data sources and generating personalized recommendations.

## Features

- **Data Collection**: Scrapes posts and events from Reddit, Instagram, Eventbrite, and other sources
- **Content Classification**: Uses AI to categorize content and tag with relevant vibes
- **Smart Ranking**: Scores items based on originality, social proof, freshness, and accessibility
- **Personalized Curation**: Generates themed day plans and interactive maps

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=your_user_agent
   INSTAGRAM_ACCESS_TOKEN=your_instagram_token
   INSTAGRAM_CLIENT_ID=your_instagram_client_id
   INSTAGRAM_CLIENT_SECRET=your_instagram_client_secret
   EVENTBRITE_API_KEY=your_eventbrite_key
   OPENAI_API_KEY=your_openai_key
   ```

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Scrape data from various sources
2. Classify and rank the items
3. Generate recommendations
4. Save results to a JSON file

## Output

The results are saved in a JSON file with the following structure:
```json
{
  "timestamp": "2024-03-04T12:00:00",
  "total_items": 100,
  "ranked_items": [...],
  "recommendations": {
    "morning": {...},
    "afternoon": {...},
    "evening": {...},
    "map": {...}
  }
}
```

## Customization

You can modify the following files to customize the agent:
- `config.py`: Adjust scraping parameters, categories, and weights
- `scraper.py`: Add new data sources
- `classifier.py`: Modify classification criteria
- `ranker.py`: Adjust ranking algorithms
- `curator.py`: Change recommendation generation

## Contributing

Feel free to submit issues and enhancement requests! 