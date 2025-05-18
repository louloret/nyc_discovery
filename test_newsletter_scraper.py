from scraper import NYCScraper
from config import NEWSLETTER_CONFIG, CATEGORIES
import json
from datetime import datetime
import re
import os
import openai

def extract_event_time(content):
    """Extract time information from content."""
    # Common time patterns
    time_patterns = [
        r'(\d{1,2}:\d{2}(?:\s*[ap]m)?)',  # 7:15pm or 7:15 pm
        r'(\d{1,2}(?::\d{2})?\s*[ap]m)',  # 7pm or 7:00pm
        r'(\d{1,2}(?::\d{2})?\s*[AP]M)',  # 7PM or 7:00PM
        r'(?:from|starting at|begins at)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)',  # from 7pm, starting at 7:30
        r'(?:doors|show)\s+(?:at|open at)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)',  # doors at 7pm, show at 8
    ]
    
    for pattern in time_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            return matches[0]
    return "TBD"

def extract_event_date(content):
    """Extract date information from content."""
    # Common date patterns
    date_patterns = [
        r'(?:May|June|July|August|September|October|November|December)\s+\d{1,2}(?:\s*-\s*\d{1,2})?',  # May 14 or May 14-16
        r'\d{1,2}/\d{1,2}(?:\s*-\s*\d{1,2}/\d{1,2})?',  # 5/14 or 5/14-5/16
        r'\d{1,2}-\d{1,2}(?:\s*-\s*\d{1,2})?',  # 5-14 or 5-14-16
        r'(?:this|next|coming)\s+(?:weekend|week|month)',  # this weekend, next week
        r'(?:today|tomorrow|tonight)',  # today, tomorrow, tonight
        r'(?:weekend|week)\s+of\s+(?:May|June|July|August|September|October|November|December)',  # weekend of May
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            return matches[0]
    return "TBD"

def extract_event_location(content):
    """Extract location information from content."""
    # Common location patterns
    location_patterns = [
        r'(?:at|in|@)\s+([A-Za-z0-9\s\-\'\.]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Park|Plaza|Square|Theater|Theatre|Center|Club|Bar|Restaurant|Cafe|Garden|Museum|Gallery))',
        r'(?:located at|venue:)\s+([A-Za-z0-9\s\-\'\.]+)',
        r'(?:address:)\s+([A-Za-z0-9\s\-\'\.]+)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    return "TBD"

def extract_event_price(content):
    """Extract price information from content."""
    # Common price patterns
    price_patterns = [
        r'(?:tickets?|admission|entry|cover)\s+(?:are|is|costs?|priced at)?\s*\$(\d+(?:\.\d{2})?)',
        r'\$(\d+(?:\.\d{2})?)\s+(?:tickets?|admission|entry|cover)',
        r'(?:free|no charge|complimentary)',
        r'(?:donation|suggested donation)',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            if pattern == r'(?:free|no charge|complimentary)':
                return "Free"
            elif pattern == r'(?:donation|suggested donation)':
                return "Donation"
            else:
                return f"${matches[0]}"
    return "TBD"

def categorize_event(title, content):
    """Categorize event based on title and content."""
    # Combine title and content for better categorization
    text = (title + " " + content).lower()
    
    # Define category keywords
    category_keywords = {
        'Art': ['art', 'exhibition', 'gallery', 'museum', 'design', 'show', 'display', 'installation', 'theater', 'theatre', 'play', 'performance', 'musical', 'drama', 'comedy'],
        'Outdoors': ['outdoor', 'park', 'garden', 'hike', 'walk', 'festival', 'fair', 'market'],
        'Food': ['food', 'restaurant', 'dining', 'tasting', 'culinary', 'drink', 'wine', 'beer', 'cocktail'],
        'Nightlife': ['night', 'club', 'bar', 'party', 'music', 'concert', 'dj', 'dance'],
        'Workshops': ['workshop', 'class', 'learn', 'tutorial', 'course', 'lesson', 'training'],
        'Talks': ['talk', 'lecture', 'discussion', 'panel', 'conference', 'seminar', 'presentation'],
        'Only-in-NYC': ['nyc', 'new york', 'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island']
    }
    
    # Count keyword matches for each category
    category_scores = {category: 0 for category in CATEGORIES}
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                category_scores[category] += 1
    
    # Return the category with the highest score
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    return "Uncategorized"

def summarize_content(content):
    """Summarize event content using OpenAI API (gpt-4o, v1.x interface), fallback to first 200 chars if unavailable."""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the following event description in 1-2 sentences, focusing on what, when, where, and why someone might attend."},
                {"role": "user", "content": content}
            ],
            max_tokens=80,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"OpenAI API error: {e}. Falling back to first 200 chars.")
    # Fallback
    return content[:200] + ('...' if len(content) > 200 else '')

def test_newsletter_scraping():
    print("Starting newsletter scraping test...")
    scraper = NYCScraper()
    all_events = []
    
    print("\nArticles from Substack sources:")
    for source_name, source_info in NEWSLETTER_CONFIG['sources'].items():
        if source_info['type'] == 'substack':
            print(f"\nScraping {source_name}...")
            articles = scraper.scrape_substack(source_info['url'])
            if articles:
                all_events.extend(articles)
            else:
                print("No articles found.")
    
    print("\nArticles from blog sources:")
    for source_name, source_info in NEWSLETTER_CONFIG['sources'].items():
        if source_info['type'] == 'blog':
            print(f"\nScraping {source_name}...")
            articles = scraper.scrape_blog(source_info['url'])
            if articles:
                all_events.extend(articles)
            else:
                print("No articles found.")
    
    # Save articles as JSON log file
    log_file = f"nyc_discovery/nyc_events_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    print(f"\nArticles JSON log file saved: {log_file}")
    
    # Generate markdown output with date and time
    output_file = f"nyc_discovery/nyc_events_newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    scraper.generate_markdown(all_events, output_file)
    print(f"\nMarkdown file generated: {output_file}")
    
    # Print summary
    print("\nEvent Summary:")
    print("=" * 80)
    total_events = sum(len(article.get('extracted_events', [])) for article in all_events)
    print(f"Total events found: {total_events}")

# Utility: regenerate markdown from a saved JSON log file
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--from-json':
        # Usage: python test_newsletter_scraper.py --from-json path/to/log.json
        json_path = sys.argv[2]
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        scraper = NYCScraper()
        output_file = f"nyc_discovery/nyc_events_newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        scraper.generate_markdown(articles, output_file)
        print(f"Markdown file generated from JSON: {output_file}")
    else:
        test_newsletter_scraping() 