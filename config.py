import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reddit API Configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT')
}

# Instagram API Configuration
INSTAGRAM_CONFIG = {
    'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
    'client_id': os.getenv('INSTAGRAM_CLIENT_ID'),
    'client_secret': os.getenv('INSTAGRAM_CLIENT_SECRET')
}

# Eventbrite API Configuration
EVENTBRITE_CONFIG = {
    'api_key': os.getenv('EVENTBRITE_API_KEY')
}

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Target Sources
TARGET_SOURCES = {
    'reddit': ['AskNYC', 'nyc'],
    'instagram': ['nyc', 'nycsecret', 'nycspots'],
    'newsletters': ['The Skint', 'Murmrr'],
    'event_platforms': ['Eventbrite', 'TimeOut']
}

# Scraping Configuration
SCRAPING_CONFIG = {
    'post_limit': 1000,
    'time_filter': 'month',
    'min_score': 5,
    'min_comments': 3,
    'keywords': [
        'hidden gem',
        'underrated',
        'weirdest place',
        'you have to check out',
        'what\'s something only locals know'
    ]
}

# Classification Configuration
CATEGORIES = [
    'Art',
    'Outdoors',
    'Food',
    'Nightlife',
    'Workshops',
    'Talks',
    'Only-in-NYC'
]

VIBES = [
    'romantic',
    'surreal',
    'quirky',
    'intellectual',
    'adventurous',
    'relaxing',
    'energetic'
]

CLASSIFICATION_PROMPT = """
Analyze the following content and classify it into one of these categories: {categories}
Also tag it with relevant vibes from: {vibes}

Content: {content}

Please respond with a JSON object containing:
1. category (string)
2. vibes (array of strings)
3. confidence_score (float)
"""

# Ranking Configuration
RANKING_WEIGHTS = {
    'originality': 0.3,
    'social_proof': 0.3,
    'freshness': 0.2,
    'accessibility': 0.2
}

# Clustering Configuration
CLUSTERING_CONFIG = {
    'min_cluster_size': 5,
    'min_samples': 3,
    'metric': 'cosine'
}

# Curation Configuration
CURATION_PROMPT = """
Based on the following collection of places and events, create:
1. A themed day plan
2. Interactive map coordinates
3. Accessibility notes
4. Cost estimates
5. Time recommendations

Places and Events: {items}

Please provide a structured response with these five sections.
""" 