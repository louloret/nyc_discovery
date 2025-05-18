import praw
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import REDDIT_CONFIG, INSTAGRAM_CONFIG, EVENTBRITE_CONFIG, SCRAPING_CONFIG, TARGET_SOURCES, NEWSLETTER_CONFIG
import re
import openai

class NYCScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CONFIG['client_id'],
            client_secret=REDDIT_CONFIG['client_secret'],
            user_agent=REDDIT_CONFIG['user_agent']
        )
        # Initialize Selenium for JavaScript-heavy sites
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

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

    def scrape_substack(self, url: str) -> List[Dict[str, Any]]:
        """Scrape content from a Substack newsletter."""
        articles = []
        try:
            # Get the RSS feed URL from config
            source_info = next((info for name, info in NEWSLETTER_CONFIG['sources'].items() if info['url'] == url), None)
            if source_info and 'rss_url' in source_info:
                feed_url = source_info['rss_url']
            else:
                # Fallback to default RSS URL format
                feed_url = f"{url}/feed.xml"
            
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                # Try alternative RSS URL format
                feed_url = f"{url}/feed"
                feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:NEWSLETTER_CONFIG['scraping']['max_articles']]:
                # Check if the article is within our date range
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6])
                    if (datetime.now() - pub_date).days <= NEWSLETTER_CONFIG['scraping']['date_range_days']:
                        # For coolstuffnyc, use Selenium to get full content
                        content = entry.summary
                        if 'coolstuffnyc' in url:
                            try:
                                self.driver.get(entry.link)
                                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "body")))
                                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                                content_elem = soup.find('div', class_='body')
                                if content_elem:
                                    content = content_elem.get_text(separator='\n', strip=True)
                            except Exception as e:
                                print(f"Error getting full content for {entry.link}: {str(e)}")
                        
                        # Use GPT-4 to extract and summarize events
                        try:
                            response = self.extract_events_with_gpt4(content)
                            if response:
                                articles.append({
                                    'source': 'substack',
                                    'title': entry.title,
                                    'content': content,
                                    'url': entry.link,
                                    'published_date': pub_date.isoformat(),
                                    'author': entry.author if hasattr(entry, 'author') else None,
                                    'extracted_events': response,
                                    'gpt4_raw': response
                                })
                        except Exception as e:
                            print(f"Error extracting events with GPT-4: {str(e)}")
                            # Fallback to basic article format if GPT-4 extraction fails
                            # Optionally, you could run regex extraction here and add it to the article
                            articles.append({
                                'source': 'substack',
                                'title': entry.title,
                                'content': content,
                                'url': entry.link,
                                'published_date': pub_date.isoformat(),
                                'author': entry.author if hasattr(entry, 'author') else None,
                                'regex_fallback': True
                            })
        except Exception as e:
            print(f"Error scraping Substack {url}: {str(e)}")
        return articles

    def scrape_blog(self, url: str) -> List[Dict[str, Any]]:
        """Scrape content from a blog."""
        articles = []
        try:
            # Get source info from config
            source_info = next((info for name, info in NEWSLETTER_CONFIG['sources'].items() if info['url'] == url), None)
            
            # Add headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # First try with requests
            response = requests.get(url, headers=headers, timeout=NEWSLETTER_CONFIG['scraping']['request_timeout'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
            else:
                # If requests fails, try with Selenium
                self.driver.get(url)
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Get article elements using source-specific selector if available
            article_elements = []
            if source_info and 'article_selector' in source_info:
                article_elements = soup.select(source_info['article_selector'])
            else:
                # Fallback to common article patterns
                for selector in ['article', '.post', '.entry', '.article']:
                    elements = soup.select(selector)
                    if elements:
                        article_elements = elements
                        break
            
            for element in article_elements[:NEWSLETTER_CONFIG['scraping']['max_articles']]:
                # Try different title patterns
                title = None
                for title_tag in ['h1', 'h2', 'h3', 'h4']:
                    title_elem = element.find(title_tag)
                    if title_elem:
                        title = title_elem.text.strip()
                        break
                
                # Try different content patterns
                content = None
                for content_class in ['content', 'entry-content', 'post-content', 'article-content']:
                    content_elem = element.find(['div', 'p'], class_=content_class)
                    if content_elem:
                        content = content_elem.text.strip()
                        break
                
                # Try different date patterns
                date = None
                for date_class in ['date', 'published', 'post-date']:
                    date_elem = element.find(['time', 'span'], class_=date_class)
                    if date_elem:
                        date = date_elem.get('datetime', '')
                        break
                
                if title and content and len(content) >= NEWSLETTER_CONFIG['scraping']['min_content_length']:
                    # Use GPT-4 to extract and summarize events
                    try:
                        response = self.extract_events_with_gpt4(content)
                        if response:
                            articles.append({
                                'source': 'blog',
                                'title': title,
                                'content': content,
                                'url': url,
                                'published_date': date,
                                'extracted_events': response,
                                'gpt4_raw': response
                            })
                    except Exception as e:
                        print(f"Error extracting events with GPT-4: {str(e)}")
                        # Fallback to basic article format if GPT-4 extraction fails
                        articles.append({
                            'source': 'blog',
                            'title': title,
                            'content': content,
                            'url': url,
                            'published_date': date
                        })
        except Exception as e:
            print(f"Error scraping blog {url}: {str(e)}")
        return articles

    def scrape_newsletters(self) -> List[Dict[str, Any]]:
        """Scrape content from all configured newsletters."""
        all_articles = []
        
        for source_name, source_info in NEWSLETTER_CONFIG['sources'].items():
            if source_info['type'] == 'substack':
                articles = self.scrape_substack(source_info['url'])
            else:  # blog
                articles = self.scrape_blog(source_info['url'])
            
            # Add source metadata
            for article in articles:
                article['source_name'] = source_name
                article['source_category'] = source_info['category']
            
            all_articles.extend(articles)
        
        return all_articles

    def scrape_all(self) -> List[Dict[str, Any]]:
        """Scrape data from all sources."""
        all_data = []
        all_data.extend(self.scrape_reddit())
        all_data.extend(self.scrape_instagram())
        all_data.extend(self.scrape_eventbrite())
        all_data.extend(self.scrape_newsletters())
        return all_data

    def generate_markdown(self, articles, output_file):
        """Generate markdown output from scraped articles."""
        markdown_content = ["# NYC Events Newsletter\n"]
        
        # Group articles by source
        substack_articles = [a for a in articles if a.get('source') == 'substack']
        blog_articles = [a for a in articles if a.get('source') == 'blog']
        
        # Substack Sources section
        if substack_articles:
            markdown_content.append("\n## 📰 Substack Sources\n")
            for article in substack_articles:
                markdown_content.append(f"\n### {article['title']}")
                if article.get('published_date'):
                    # Format published date as YYYY-MM-DD
                    pub_date = article['published_date'].split('T')[0]
                    markdown_content.append(f"- **Published:** {pub_date}")
                if article.get('url'):
                    markdown_content.append(f"- **URL:** [Read the article]({article['url']})")
                
                if article.get('extracted_events'):
                    markdown_content.append("\n#### Events (GPT-4o Extraction)")
                    markdown_content.append("| Event Title | Date/Time | Location | Price | Category |")
                    markdown_content.append("|------------|-----------|----------|-------|----------|")
                    
                    for event in article['extracted_events']:
                        title = event.get('title', 'N/A')
                        date_time = event.get('date_time', 'TBD')
                        location = event.get('location', 'N/A')
                        price = event.get('price', 'N/A')
                        category = event.get('category', 'N/A')
                        markdown_content.append(f"| {title} | {date_time} | {location} | {price} | {category} |")
                    
                    markdown_content.append("\n**Event Descriptions:**")
                    for event in article['extracted_events']:
                        title = event.get('title', 'N/A')
                        date_time = event.get('date_time', 'TBD')
                        location = event.get('location', 'N/A')
                        description = event.get('description', 'N/A')
                        markdown_content.append(f"- **{title}** ({date_time}, {location}): {description}")
                
                markdown_content.append("\n---")
        
        # Blog Sources section
        if blog_articles:
            markdown_content.append("\n## 📝 Blog Sources\n")
            for article in blog_articles:
                markdown_content.append(f"\n### {article['title']}")
                if article.get('published_date'):
                    # Format published date as YYYY-MM-DD
                    pub_date = article['published_date'].split('T')[0]
                    markdown_content.append(f"- **Published:** {pub_date}")
                if article.get('url'):
                    markdown_content.append(f"- **URL:** [Read the article]({article['url']})")
                
                if article.get('extracted_events'):
                    markdown_content.append("\n#### Events (GPT-4o Extraction)")
                    markdown_content.append("| Event Title | Date/Time | Location | Price | Category |")
                    markdown_content.append("|------------|-----------|----------|-------|----------|")
                    
                    for event in article['extracted_events']:
                        title = event.get('title', 'N/A')
                        date_time = event.get('date_time', 'TBD')
                        location = event.get('location', 'N/A')
                        price = event.get('price', 'N/A')
                        category = event.get('category', 'N/A')
                        markdown_content.append(f"| {title} | {date_time} | {location} | {price} | {category} |")
                    
                    markdown_content.append("\n**Event Descriptions:**")
                    for event in article['extracted_events']:
                        title = event.get('title', 'N/A')
                        date_time = event.get('date_time', 'TBD')
                        location = event.get('location', 'N/A')
                        description = event.get('description', 'N/A')
                        markdown_content.append(f"- **{title}** ({date_time}, {location}): {description}")
                
                markdown_content.append("\n---")
        
        # Summary section
        total_events = sum(len(article.get('extracted_events', [])) for article in articles)
        markdown_content.append(f"\n## 📊 Event Summary\n")
        markdown_content.append(f"\n**Total events found:** {total_events}\n")
        markdown_content.append("\n---")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))

    def extract_events_with_gpt4(self, content: str) -> List[Dict[str, Any]]:
        """Extract events from content using GPT-4."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """Extract all events from the content and return them as a JSON array. Each event should have:
                    - title: The event title
                    - date_time: The event date and time in YYYY-MM-DD format (infer from article content, not from article publish date)
                    - location: The event location
                    - description: A brief description of the event
                    - price: The event price (if available)
                    - category: The event category (Art, Food, Shopping, etc.)
                    
                    Clean up the data:
                    - Remove any special characters from titles
                    - Standardize location format to include neighborhood/area
                    - Convert relative dates to actual dates (e.g. 'this weekend' -> YYYY-MM-DD)
                    - Format prices consistently
                    - Categorize events appropriately
                    
                    For dates:
                    - Use YYYY-MM-DD format
                    - If time is available, append it after the date (YYYY-MM-DD HH:MMam/pm)
                    - If only a date range is given, use the start date
                    - If no specific date is found, use 'TBD'"""},
                    {"role": "user", "content": content}
                ],
                temperature=0.7
            )
            
            # Get the response content
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                # First try to parse the entire response as JSON
                events = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        events = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        print(f"Error parsing JSON from response: {response_text}")
                        return []
                else:
                    print(f"No JSON array found in response: {response_text}")
                    return []
            
            # Validate and clean up the events
            cleaned_events = []
            for event in events:
                if not isinstance(event, dict):
                    continue
                    
                cleaned_event = {
                    'title': str(event.get('title', 'N/A')).strip(),
                    'date_time': str(event.get('date_time', 'N/A')).strip(),
                    'location': str(event.get('location', 'N/A')).strip(),
                    'description': str(event.get('description', 'N/A')).strip(),
                    'price': str(event.get('price', 'N/A')).strip(),
                    'category': str(event.get('category', 'N/A')).strip()
                }
                cleaned_events.append(cleaned_event)
            
            return cleaned_events
            
        except Exception as e:
            print(f"Error extracting events with GPT-4: {str(e)}")
            return [] 