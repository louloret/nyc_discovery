import os
from datetime import datetime
import glob

def get_latest_file(pattern):
    """Get the most recent file matching the pattern."""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def read_markdown(file_path):
    """Read markdown content from file."""
    if not file_path or not os.path.exists(file_path):
        return ""
    with open(file_path, 'r') as f:
        return f.read()

def combine_summaries():
    """Combine blog and Reddit event summaries into a single markdown file."""
    # Get latest files
    blog_file = get_latest_file("nyc_events_newsletter_*.md")
    reddit_file = get_latest_file("nyc_cultural_events_*.md")
    
    if not blog_file and not reddit_file:
        print("No markdown files found!")
        return
    
    # Generate combined markdown
    current_date = datetime.now().strftime("%B %d, %Y")
    combined_md = f"# NYC Events Summary - {current_date}\n\n"
    
    # Add blog events section
    if blog_file:
        blog_content = read_markdown(blog_file)
        if blog_content:
            combined_md += "## 📰 Blog & Newsletter Events\n\n"
            # Skip the title if it exists in the content
            if blog_content.startswith("#"):
                blog_content = blog_content[blog_content.find("\n")+1:]
            combined_md += blog_content + "\n\n"
    
    # Add Reddit events section
    if reddit_file:
        reddit_content = read_markdown(reddit_file)
        if reddit_content:
            combined_md += "## 🔴 Reddit Cultural Events\n\n"
            # Skip the title if it exists in the content
            if reddit_content.startswith("#"):
                reddit_content = reddit_content[reddit_content.find("\n")+1:]
            combined_md += reddit_content
    
    # Save combined file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"nyc_events_combined_{timestamp}.md"
    
    with open(output_file, 'w') as f:
        f.write(combined_md)
    
    print(f"Combined summary saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    combine_summaries() 