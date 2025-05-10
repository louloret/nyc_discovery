import praw
import config
from datetime import datetime, timedelta
from pprint import pprint
import re

def parse_relative_date(date_str):
    """Convert relative date strings to datetime objects."""
    today = datetime.now()
    date_str = date_str.lower()
    
    if date_str == 'tonight':
        return today
    elif date_str == 'tomorrow':
        return today + timedelta(days=1)
    elif date_str == 'this weekend':
        # Find the next Saturday
        days_until_saturday = (5 - today.weekday()) % 7
        return today + timedelta(days=days_until_saturday)
    elif date_str == 'next weekend':
        # Find the Saturday after next
        days_until_saturday = (5 - today.weekday()) % 7
        return today + timedelta(days=days_until_saturday + 7)
    elif date_str.startswith('this '):
        day = date_str.split('this ')[1]
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        if day in days:
            target_day = days[day]
            current_day = today.weekday()
            days_ahead = (target_day - current_day) % 7
            return today + timedelta(days=days_ahead)
    elif date_str.startswith('next '):
        day = date_str.split('next ')[1]
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        if day in days:
            target_day = days[day]
            current_day = today.weekday()
            days_ahead = (target_day - current_day) % 7 + 7
            return today + timedelta(days=days_ahead)
    
    # Try to parse specific dates
    try:
        # Handle month day format (e.g., "May 15th")
        month_day_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?'
        match = re.search(month_day_pattern, date_str, re.IGNORECASE)
        if match:
            month_str = match.group(0).split()[0]
            day = int(match.group(1))
            month = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }[month_str[:3].lower()]
            year = today.year
            # If the date is in the past, assume it's for next year
            if month < today.month or (month == today.month and day < today.day):
                year += 1
            return datetime(year, month, day)
    except:
        pass
    
    return None

def extract_date(text):
    """Extract date information from text using common patterns."""
    # Common date patterns
    patterns = [
        r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?',
        r'\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)',
        r'tonight',
        r'tomorrow',
        r'this weekend',
        r'next weekend',
        r'this (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'next (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

def categorize_event(title, description):
    """Categorize event based on keywords in title and description."""
    text = (title + " " + description).lower()
    
    categories = {
        'Music': ['concert', 'music', 'band', 'dj', 'live music', 'performance', 'jazz', 'rock', 'hip hop', 'electronic', 'classical', 'opera'],
        'House Music': ['house music', 'house party', 'deep house', 'tech house', 'afro house', 'soulful house', 'disco house', 'acid house', 'progressive house', 'minimal house'],
        'Art': ['art', 'exhibition', 'gallery', 'museum', 'show', 'display', 'installation', 'sculpture', 'painting', 'photography', 'digital art'],
        'Film': [
            # General film terms
            'movie', 'film', 'cinema', 'screening', 'documentary', 'short film', 'film festival', 
            'indie film', 'foreign film', 'classic film', 'arthouse', 'film series', 'movie night',
            # Film events
            'premiere', 'opening night', 'film screening', 'movie screening', 'film showing',
            'film festival', 'film series', 'film program', 'film retrospective', 'film marathon',
            'film club', 'film society', 'film discussion', 'film talk', 'film lecture',
            'film workshop', 'film class', 'film making', 'film production',
            # Film types
            'documentary', 'doc', 'short film', 'feature film', 'indie film', 'independent film',
            'foreign film', 'international film', 'classic film', 'silent film', 'experimental film',
            'animation', 'animated film', 'live action', 'drama', 'comedy', 'horror', 'thriller',
            'sci-fi', 'science fiction', 'romance', 'action', 'adventure', 'fantasy',
            # Film venues
            'theater', 'cinema', 'movie theater', 'film forum', 'ifc', 'angelika', 'metrograph',
            'quad cinema', 'bam', 'nighthawk', 'alamo drafthouse', 'spectacle', 'syndicated',
            'light industry', 'microscope', 'union docs', 'maysles'
        ],
        'Poetry': ['poetry', 'poem', 'poet', 'reading', 'slam', 'open mic', 'spoken word', 'verse', 'poetry night', 'poetry reading', 'poetry slam'],
        'Food': ['food', 'restaurant', 'dining', 'tasting', 'culinary', 'cooking', 'wine', 'beer', 'cocktail', 'brunch', 'dinner', 'lunch', 'food festival'],
        'Nightlife': ['party', 'club', 'bar', 'night', 'dance', 'drinks', 'lounge', 'speakeasy', 'nightclub', 'after hours'],
        'Workshop': ['workshop', 'class', 'learning', 'tutorial', 'training', 'seminar', 'lecture', 'course', 'masterclass', 'skillshare'],
        'Sports': ['sports', 'game', 'tournament', 'match', 'competition', 'fitness', 'yoga', 'running', 'cycling', 'basketball', 'baseball', 'soccer'],
        'Theater': ['theater', 'theatre', 'play', 'show', 'performance', 'drama', 'musical', 'broadway', 'off-broadway', 'improv'],
        'Comedy': ['comedy', 'standup', 'stand-up', 'jokes', 'laugh', 'improv', 'sketch', 'open mic'],
        'Outdoor': ['outdoor', 'park', 'hiking', 'walking', 'tour', 'explore', 'nature', 'garden', 'beach', 'rooftop', 'picnic'],
        'Dance': ['dance', 'ballet', 'contemporary', 'hip hop', 'salsa', 'tango', 'ballroom', 'tap dance'],
        'Literary': ['book', 'reading', 'poetry', 'author', 'book club', 'literature', 'writing', 'poetry slam'],
        'Technology': ['tech', 'technology', 'coding', 'hackathon', 'startup', 'innovation', 'digital', 'vr', 'ar', 'ai'],
        'Fashion': ['fashion', 'style', 'runway', 'design', 'clothing', 'accessories', 'pop-up shop'],
        'Wellness': ['wellness', 'meditation', 'mindfulness', 'spa', 'massage', 'healing', 'holistic', 'wellbeing'],
        'Family': ['family', 'kids', 'children', 'family-friendly', 'parent', 'toddler', 'baby'],
        'Networking': ['networking', 'meetup', 'social', 'community', 'professional', 'business', 'career'],
        'Cultural': ['cultural', 'heritage', 'tradition', 'festival', 'celebration', 'holiday', 'ethnic']
    }
    
    event_categories = []
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            event_categories.append(category)
    
    return event_categories if event_categories else ['Other']

def determine_location(title, description):
    """Determine the location/neighborhood of the event."""
    text = (title + " " + description).lower()
    
    locations = {
        'Manhattan': ['manhattan', 'midtown', 'downtown', 'uptown', 'soho', 'chelsea', 'harlem', 'upper east side', 'upper west side', 'lower east side', 'lower west side', 'financial district', 'tribeca', 'noho', 'nolita', 'gramercy', 'murray hill', 'kips bay', 'east village', 'west village', 'greenwich village', 'meatpacking district', 'hell\'s kitchen', 'clinton', 'lincoln center', 'columbus circle', 'times square',
            # Film venues
            'film forum', 'ifc center', 'angelika', 'film at lincoln center', 'metrograph', 'quad cinema', 
            'moma', 'whitney museum', 'mcc', 'mcc theater', 'film society', 'film society of lincoln center'],
        'Brooklyn': [
            # Neighborhoods
            'brooklyn', 'williamsburg', 'dumbo', 'park slope', 'bushwick', 'bed-stuy', 'bedford-stuyvesant', 
            'crown heights', 'prospect heights', 'greenpoint', 'red hook', 'gowanus', 'carroll gardens', 
            'cobble hill', 'boerum hill', 'sunset park', 'bay ridge', 'brighton beach', 'coney island', 
            'sheepshead bay', 'flatbush', 'prospect park', 'fort greene', 'clinton hill', 'brooklyn heights',
            # Venues
            'nighthawk', 'nighthawk cinema', 'nighthawk prospect park', 'nighthawk williamsburg',
            'elsewhere', 'elsewhere brooklyn', 'elsewhere hall', 'elsewhere zone one',
            'brooklyn steel', 'brooklyn mirage', 'avante gardner', 'knockdown center',
            'music hall of williamsburg', 'rough trade', 'baby\'s all right', 'brooklyn bowl',
            'house of yes', '3 dollar bill', 'good room', 'silo', 'sisters', 'trans pecos',
            'market hotel', 'union pool', 'brooklyn made', 'brooklyn monarch', 'brooklyn paramount',
            'warsaw', 'berry park', 'brooklyn expo center', 'zero space', 'brooklyn museum',
            'brooklyn academy of music', 'bam', 'st. ann\'s warehouse', 'national sawdust',
            'pioneer works', 'industry city', 'brooklyn navy yard', 'brooklyn bridge park',
            'domino park', 'mccarren park', 'prospect park bandshell', 'brooklyn botanic garden',
            # Film venues
            'syndicated', 'syndicated bar theater', 'syndicated bar theater kitchen', 'syndicated bar',
            'alamo drafthouse', 'alamo drafthouse brooklyn', 'alamo drafthouse williamsburg',
            'bam rose cinemas', 'bam cinema', 'bam film', 'bam film festival',
            'spectacle theater', 'spectacle', 'spectacle cinema', 'spectacle film',
            'light industry', 'light industry film', 'light industry cinema',
            'microscope gallery', 'microscope', 'microscope cinema',
            'union docs', 'union documentary', 'union docs center',
            'maysles documentary center', 'maysles cinema', 'maysles',
            'brooklyn film festival', 'brooklyn film', 'brooklyn cinema',
            'brooklyn international film festival', 'biff'
        ],
        'Queens': ['queens', 'astoria', 'long island city', 'lic', 'flushing', 'forest hills', 'rego park', 'jackson heights', 'elmhurst', 'corona', 'sunnyside', 'woodside', 'maspeth', 'middle village', 'ridgewood', 'glendale', 'bayside', 'douglaston', 'little neck', 'jamaica', 'rockaway', 'howard beach'],
        'Bronx': ['bronx', 'yankee stadium', 'bronx zoo', 'riverdale', 'kingsbridge', 'fordham', 'morris park', 'pelham bay', 'throgs neck', 'city island', 'hunts point', 'concourse', 'bedford park'],
        'Staten Island': ['staten island', 'st. george', 'tompkinsville', 'stapleton', 'rosebank', 'fort wadsworth', 'great kills', 'tottenville']
    }
    
    for location, keywords in locations.items():
        if any(keyword in text for keyword in keywords):
            return location
    
    return 'Location Not Specified'

def calculate_popularity_score(post):
    """Calculate a popularity score based on upvotes and comments."""
    # Weight upvotes more than comments
    return (post.score * 2) + post.num_comments

def find_events(days_ahead=14, include_recent=True):
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=config.REDDIT_CONFIG['client_id'],
        client_secret=config.REDDIT_CONFIG['client_secret'],
        user_agent=config.REDDIT_CONFIG['user_agent']
    )
    
    # List of relevant subreddits
    subreddits = [
        # General NYC
        'nyc', 'Brooklyn', 'AskNYC', 'NYCevents',
        # Music
        'NYCmeetups', 'NYCConcerts', 'NYCMusic', 'NYCJazz', 'NYCClassical', 'NYCDance',
        'house', 'techno', 'electronicmusic', 'avesnyc', 'brooklynelectronic',
        # Film
        'NYCFilm', 'FilmSociety', 'TrueFilm', 'indiefilm', 'Documentaries',
        'MovieTheaterEmployees', 'AMCsAList', 'RegalUnlimited',
        'FilmNoir', 'Criterion', 'TrueFilm', 'MovieDetails', 'FilmClub',
        'FilmFestivals', 'Documentary', 'ShortFilm', 'IndieCinema',
        # Poetry & Literary
        'Poetry', 'NYCPoetry', 'PoetrySlam', 'spokenword', 'NYCLiterary',
        # Arts & Culture
        'NYCArt', 'NYCComedy', 'NYCTheatre', 'NYCFood', 'NYCBeer', 'NYCWhiskey',
        # Lifestyle
        'NYCFitness', 'NYCFreeAndCheap', 'NYCPhotography',
        # Brooklyn specific
        'BrooklynEvents', 'BrooklynMeetups', 'BrooklynMusic', 'BrooklynArt'
    ]
    
    # Keywords that might indicate events
    event_keywords = [
        'event', 'festival', 'concert', 'show', 'exhibition',
        'party', 'meetup', 'workshop', 'class', 'tour',
        'happening', 'this weekend', 'tonight', 'tomorrow',
        'free event', 'tickets', 'RSVP', 'performance',
        'screening', 'opening', 'launch', 'premiere',
        'reading', 'slam', 'open mic', 'house music',
        'dj', 'film', 'movie', 'cinema', 'poetry',
        # Film specific
        'film screening', 'movie screening', 'film festival', 'film series',
        'film program', 'film retrospective', 'film marathon', 'film club',
        'film society', 'film discussion', 'film talk', 'film lecture',
        'film workshop', 'film class', 'film making', 'film production',
        'premiere', 'opening night', 'documentary', 'short film',
        'indie film', 'foreign film', 'classic film', 'arthouse',
        # Brooklyn specific venues
        'nighthawk', 'elsewhere', 'brooklyn steel', 'brooklyn mirage',
        'avante gardner', 'knockdown center', 'music hall of williamsburg',
        'rough trade', 'baby\'s all right', 'brooklyn bowl', 'house of yes',
        '3 dollar bill', 'good room', 'silo', 'sisters', 'trans pecos',
        'market hotel', 'union pool', 'brooklyn made', 'brooklyn monarch',
        'brooklyn paramount', 'warsaw', 'berry park', 'brooklyn expo center',
        'zero space', 'brooklyn museum', 'brooklyn academy of music', 'bam',
        'st. ann\'s warehouse', 'national sawdust', 'pioneer works',
        'industry city', 'brooklyn navy yard', 'brooklyn bridge park',
        'domino park', 'mccarren park', 'prospect park bandshell',
        'brooklyn botanic garden', 'nighthawk cinema', 'nighthawk prospect park',
        'nighthawk williamsburg', 'syndicated', 'syndicated bar theater',
        'alamo drafthouse', 'alamo drafthouse brooklyn', 'spectacle theater',
        'light industry', 'microscope gallery', 'union docs', 'maysles'
    ]
    
    print(f"Searching for events in NYC and Brooklyn (next {days_ahead} days)...")
    print("-" * 80)
    
    events = []
    today = datetime.now()
    end_date = today + timedelta(days=days_ahead)
    recent_date = today - timedelta(days=7) if include_recent else today
    
    for subreddit_name in subreddits:
        print(f"\nSearching in r/{subreddit_name}...")
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Search in hot, new, and rising posts
            for post in subreddit.hot(limit=30):
                # Check if post title or text contains event-related keywords
                if any(keyword.lower() in post.title.lower() for keyword in event_keywords):
                    # Extract date information
                    date_str = extract_date(post.title + " " + post.selftext)
                    
                    # Only include if we found a date
                    if date_str:
                        event_date = parse_relative_date(date_str)
                        if event_date and (recent_date <= event_date <= end_date):
                            event = {
                                'title': post.title,
                                'date_info': date_str,
                                'date': event_date,
                                'score': post.score,
                                'comments': post.num_comments,
                                'popularity_score': calculate_popularity_score(post),
                                'posted': datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                                'url': post.url,
                                'description': post.selftext[:200] + "..." if post.selftext else "",
                                'categories': categorize_event(post.title, post.selftext),
                                'location': determine_location(post.title, post.selftext)
                            }
                            events.append(event)
            
            # Also search in new posts
            for post in subreddit.new(limit=20):
                if any(keyword.lower() in post.title.lower() for keyword in event_keywords):
                    date_str = extract_date(post.title + " " + post.selftext)
                    if date_str:
                        event_date = parse_relative_date(date_str)
                        if event_date and (recent_date <= event_date <= end_date):
                            event = {
                                'title': post.title,
                                'date_info': date_str,
                                'date': event_date,
                                'score': post.score,
                                'comments': post.num_comments,
                                'popularity_score': calculate_popularity_score(post),
                                'posted': datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                                'url': post.url,
                                'description': post.selftext[:200] + "..." if post.selftext else "",
                                'categories': categorize_event(post.title, post.selftext),
                                'location': determine_location(post.title, post.selftext)
                            }
                            events.append(event)
                        
        except Exception as e:
            print(f"Error searching r/{subreddit_name}: {str(e)}")
            continue
    
    # Sort events by date and then by popularity score
    events.sort(key=lambda x: (x['date'], -x['popularity_score']))
    
    # Print events grouped by location
    locations = {}
    for event in events:
        location = event['location']
        if location not in locations:
            locations[location] = []
        locations[location].append(event)
    
    # Print Brooklyn events first, then others
    location_order = ['Brooklyn'] + [loc for loc in locations.keys() if loc != 'Brooklyn']
    
    for location in location_order:
        if location in locations:
            print(f"\n{'='*40}")
            print(f"Events in {location}")
            print(f"{'='*40}")
            
            for event in locations[location]:
                print(f"\nTitle: {event['title']}")
                print(f"Date: {event['date_info']} ({event['date'].strftime('%Y-%m-%d')})")
                print(f"Categories: {', '.join(event['categories'])}")
                print(f"Popularity Score: {event['popularity_score']} (↑{event['score']} | 💬{event['comments']})")
                print(f"URL: {event['url']}")
                if event['description']:
                    print(f"Description: {event['description']}")
                print("-" * 80)

if __name__ == "__main__":
    find_events(include_recent=True) 