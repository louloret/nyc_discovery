import praw
import json
from datetime import datetime, timedelta
import re
from config import REDDIT_CONFIG
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_relative_date(date_str):
    """Convert relative date strings to datetime objects."""
    now = datetime.now()
    if 'today' in date_str.lower():
        return now
    elif 'tomorrow' in date_str.lower():
        return now + timedelta(days=1)
    elif 'next week' in date_str.lower():
        return now + timedelta(days=7)
    return None

def extract_date(text):
    """Extract date information from text using common patterns."""
    # Common date patterns
    patterns = [
        r'(\d{1,2}/\d{1,2})',  # MM/DD
        r'(\d{1,2}-\d{1,2})',  # MM-DD
        r'(\w+ \d{1,2})',      # Month DD
        r'(\d{1,2}:\d{2}(?:am|pm))',  # Time
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    return None

def is_within_next_two_weeks(date_str):
    """Check if a date string is within the next two weeks."""
    now = datetime.now()
    two_weeks_later = now + timedelta(days=14)
    
    # Try to parse the date string
    try:
        # Handle MM/DD format
        if '/' in date_str:
            month, day = map(int, date_str.split('/'))
            event_date = datetime(now.year, month, day)
        # Handle Month DD format
        elif any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            for month_name, month_num in month_map.items():
                if month_name in date_str.lower():
                    day = int(re.search(r'\d+', date_str).group())
                    event_date = datetime(now.year, month_num, day)
                    break
        else:
            return False
            
        # Check if the date is within the next two weeks
        return now <= event_date <= two_weeks_later
    except:
        return False

def determine_location(title, description):
    """Determine the location of the event based on keywords."""
    locations = {
        'Manhattan': ['manhattan', 'midtown', 'downtown', 'uptown', 'chelsea', 'soho', 'east village', 'west village'],
        'Brooklyn': ['brooklyn', 'williamsburg', 'dumbo', 'park slope', 'bushwick', 'gowanus'],
        'Queens': ['queens', 'astoria', 'long island city', 'flushing'],
        'Bronx': ['bronx', 'riverdale', 'pelham bay'],
        'Staten Island': ['staten island', 'st. george']
    }
    
    text = (title + ' ' + description).lower()
    
    for location, keywords in locations.items():
        if any(keyword in text for keyword in keywords):
            return location
            
    return 'Location Not Specified'

def calculate_popularity_score(post):
    """Calculate a popularity score based on upvotes and comments."""
    score = post.score
    comments = post.num_comments
    return score + (comments * 2)  # Weight comments more heavily

def is_cultural_event(title, description):
    """Determine if an event is cultural based on keywords."""
    cultural_keywords = {
        'music': ['concert', 'show', 'band', 'music', 'dj', 'live', 'performance', 'symphony', 'orchestra'],
        'art': ['art', 'exhibition', 'gallery', 'museum', 'design', 'craft', 'creative', 'studio'],
        'film': ['film', 'movie', 'cinema', 'screening', 'documentary', 'short film'],
        'dance': ['dance', 'ballet', 'choreography', 'performance'],
        'poetry': ['poetry', 'poem', 'reading', 'spoken word', 'slam'],
        'theater': ['theater', 'theatre', 'play', 'musical', 'drama', 'comedy', 'improv'],
        'museum': ['museum', 'exhibition', 'gallery', 'collection']
    }
    
    text = (title + ' ' + description).lower()
    
    for category, keywords in cultural_keywords.items():
        if any(keyword in text for keyword in keywords):
            return True, category
            
    return False, None

def generate_markdown(events, output_file):
    """Generate a markdown summary of events."""
    now = datetime.now()
    markdown = f"# NYC Cultural Events - {now.strftime('%B %d, %Y')}\n\n"
    
    # Group events by category
    categories = {}
    for event in events:
        category = event.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(event)
    
    # Sort categories by number of events
    sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Write each category section
    for category, category_events in sorted_categories:
        markdown += f"## {category.title()}\n\n"
        
        # Sort events by popularity score
        category_events.sort(key=lambda x: x['popularity_score'], reverse=True)
        
        for event in category_events:
            markdown += f"### {event['title']}\n"
            markdown += f"- **Date:** {event['date']}\n"
            markdown += f"- **Location:** {event['location']}\n"
            if event['description']:
                # Clean up description text
                desc = event['description'].replace('\n', ' ').strip()
                if len(desc) > 200:
                    desc = desc[:197] + "..."
                markdown += f"- **Description:** {desc}\n"
            markdown += f"- **Popularity Score:** {event['popularity_score']}\n"
            markdown += f"- **Source:** [Reddit Post]({event['url']})\n\n"
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(markdown)

def find_cultural_events(days_ahead=14, include_recent=True):
    """Find cultural events from Reddit."""
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID', REDDIT_CONFIG['client_id']),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET', REDDIT_CONFIG['client_secret']),
        user_agent=REDDIT_CONFIG['user_agent']
    )
    
    # Define relevant subreddits
    subreddits = [
        'nyc', 'Brooklyn', 'AskNYC', 'NYCevents', 'NYCmeetups',
        'NYCConcerts', 'NYCMusic', 'NYCJazz', 'NYCClassical',
        'NYCDance', 'NYCArt', 'NYCComedy', 'NYCTheatre',
        'NYCFilm', 'FilmSociety', 'TrueFilm', 'indiefilm',
        'Documentaries', 'Poetry', 'NYCPoetry', 'PoetrySlam',
        'spokenword', 'NYCLiterary'
    ]
    
    events = []
    seen_titles = set()  # To avoid duplicates
    
    print(f"Searching for cultural events in NYC for the next {days_ahead} days...")
    
    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            print(f"\nSearching in r/{subreddit_name}...")
            
            # Search recent posts
            for post in subreddit.new(limit=100):
                # Skip if we've seen this title before
                if post.title in seen_titles:
                    continue
                    
                seen_titles.add(post.title)
                
                # Extract date information
                date = extract_date(post.title + ' ' + post.selftext)
                if not date:
                    continue
                    
                # Check if the event is within the next two weeks
                if not is_within_next_two_weeks(date):
                    continue
                
                # Check if it's a cultural event
                is_cultural, category = is_cultural_event(post.title, post.selftext)
                if not is_cultural:
                    continue
                
                # Create event object
                event = {
                    'title': post.title,
                    'date': date,
                    'location': determine_location(post.title, post.selftext),
                    'description': post.selftext,
                    'url': f"https://reddit.com{post.permalink}",
                    'popularity_score': calculate_popularity_score(post),
                    'source': 'reddit',
                    'subreddit': subreddit_name,
                    'category': category
                }
                
                events.append(event)
                
        except Exception as e:
            print(f"Error searching r/{subreddit_name}: {str(e)}")
            continue
    
    # Sort events by popularity score
    events.sort(key=lambda x: x['popularity_score'], reverse=True)
    
    # Save to JSON file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_output = f"nyc_reddit_cultural_events_{timestamp}.json"
    markdown_output = f"nyc_reddit_cultural_events_{timestamp}.md"
    
    with open(json_output, 'w') as f:
        json.dump(events, f, indent=2)
    
    # Generate markdown summary
    generate_markdown(events, markdown_output)
    
    print(f"\nFound {len(events)} cultural events in the next two weeks!")
    print(f"Results saved to {json_output} and {markdown_output}")
    
    return events

if __name__ == "__main__":
    find_cultural_events() 