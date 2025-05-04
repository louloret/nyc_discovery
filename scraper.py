import praw
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import REDDIT_CONFIG, INSTAGRAM_CONFIG, EVENTBRITE_CONFIG, SCRAPING_CONFIG, TARGET_SOURCES

class NYCScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CONFIG['client_id'],
            client_secret=REDDIT_CONFIG['client_secret'],
            user_agent=REDDIT_CONFIG['user_agent']
        )
        
    def scrape_reddit(self) -> List[Dict[str, Any]]:
        """Scrape posts from target subreddits."""
        posts = []
        for subreddit_name in TARGET_SOURCES['reddit']:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for post in subreddit.search(
                query=' OR '.join(SCRAPING_CONFIG['keywords']),
                time_filter=SCRAPING_CONFIG['time_filter'],
                limit=SCRAPING_CONFIG['post_limit']
            ):
                if post.score >= SCRAPING_CONFIG['min_score'] and post.num_comments >= SCRAPING_CONFIG['min_comments']:
                    posts.append({
                        'source': 'reddit',
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'content': post.selftext,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'comments': [comment.body for comment in post.comments[:10]]
                    })
        return posts

    def scrape_instagram(self) -> List[Dict[str, Any]]:
        """Scrape posts from Instagram using the Graph API."""
        posts = []
        base_url = 'https://graph.instagram.com/v12.0'
        
        for account in TARGET_SOURCES['instagram']:
            # Get user ID
            user_url = f"{base_url}/ig_hashtag_search"
            params = {
                'user_id': INSTAGRAM_CONFIG['client_id'],
                'q': account,
                'access_token': INSTAGRAM_CONFIG['access_token']
            }
            
            response = requests.get(user_url, params=params)
            if response.status_code == 200:
                hashtag_id = response.json()['data'][0]['id']
                
                # Get recent media
                media_url = f"{base_url}/{hashtag_id}/recent_media"
                media_params = {
                    'access_token': INSTAGRAM_CONFIG['access_token'],
                    'fields': 'caption,media_type,media_url,permalink,timestamp'
                }
                
                media_response = requests.get(media_url, params=media_params)
                if media_response.status_code == 200:
                    for media in media_response.json()['data']:
                        posts.append({
                            'source': 'instagram',
                            'account': account,
                            'caption': media.get('caption', ''),
                            'media_type': media['media_type'],
                            'url': media['permalink'],
                            'timestamp': media['timestamp']
                        })
        
        return posts

    def scrape_eventbrite(self) -> List[Dict[str, Any]]:
        """Scrape events from Eventbrite."""
        events = []
        base_url = 'https://www.eventbriteapi.com/v3'
        headers = {
            'Authorization': f"Bearer {EVENTBRITE_CONFIG['api_key']}"
        }
        
        # Search for events in NYC
        search_url = f"{base_url}/events/search"
        params = {
            'location.address': 'New York, NY',
            'sort_by': 'date',
            'start_date.range_start': (datetime.now() - timedelta(days=30)).isoformat(),
            'expand': 'venue'
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code == 200:
            for event in response.json()['events']:
                events.append({
                    'source': 'eventbrite',
                    'name': event['name']['text'],
                    'description': event['description']['text'],
                    'start_time': event['start']['local'],
                    'end_time': event['end']['local'],
                    'venue': event['venue']['name'],
                    'url': event['url'],
                    'price': event.get('ticket_availability', {}).get('minimum_ticket_price', {}).get('major_value')
                })
        
        return events

    def scrape_all(self) -> List[Dict[str, Any]]:
        """Scrape data from all sources."""
        all_data = []
        all_data.extend(self.scrape_reddit())
        all_data.extend(self.scrape_instagram())
        all_data.extend(self.scrape_eventbrite())
        return all_data 