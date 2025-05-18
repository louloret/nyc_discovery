import json
from datetime import datetime
from collections import defaultdict
import re

def load_events(json_file):
    """Load events from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def clean_text(text):
    """Clean text by removing extra whitespace and special characters."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.strip()

def format_date(date_str):
    """Format date string to a more readable format."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        return date.strftime("%B %d, %Y")
    except:
        return date_str

def categorize_events(events):
    """Categorize events by their type."""
    categories = defaultdict(list)
    
    for event in events:
        # Extract categories from the event
        event_categories = event.get('categories', [])
        if not event_categories:
            event_categories = ['Other']
            
        # Add event to each of its categories
        for category in event_categories:
            categories[category].append(event)
            
    return categories

def generate_markdown(events, output_file):
    """Generate markdown summary of events."""
    # Get current date for the title
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Start building the markdown content
    markdown = f"# NYC Events Summary: {current_date}\n\n"
    
    # Categorize events
    categorized_events = categorize_events(events)
    
    # Sort categories by number of events (descending)
    sorted_categories = sorted(categorized_events.items(), 
                             key=lambda x: len(x[1]), 
                             reverse=True)
    
    # Generate content for each category
    for category, category_events in sorted_categories:
        if not category_events:
            continue
            
        # Add category header
        markdown += f"## 🎭 **{category} Events**\n\n"
        
        # Sort events by popularity score (if available)
        sorted_events = sorted(category_events, 
                             key=lambda x: x.get('popularity_score', 0), 
                             reverse=True)
        
        # Add each event
        for event in sorted_events:
            title = clean_text(event.get('title', ''))
            date = format_date(event.get('date', ''))
            location = clean_text(event.get('location', 'Location Not Specified'))
            description = clean_text(event.get('description', ''))
            popularity = event.get('popularity_score', 0)
            
            markdown += f"### **{title}**\n"
            markdown += f"- **Date:** {date}\n"
            markdown += f"- **Location:** {location}\n"
            if description:
                markdown += f"- **Details:** {description}\n"
            if popularity > 0:
                markdown += f"- **Popularity Score:** {popularity}\n"
            markdown += "\n"
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    return output_file

def main():
    # Input and output file paths
    input_file = "nyc_reddit_events_20250518_152216.json"
    output_file = "nyc_events_summary.md"
    
    # Load events
    events = load_events(input_file)
    
    # Generate markdown summary
    output_path = generate_markdown(events, output_file)
    print(f"Summary generated and saved to: {output_path}")

if __name__ == "__main__":
    main() 