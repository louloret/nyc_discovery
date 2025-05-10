import praw
import config
from pprint import pprint

def test_reddit_connection():
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=config.REDDIT_CONFIG['client_id'],
        client_secret=config.REDDIT_CONFIG['client_secret'],
        user_agent=config.REDDIT_CONFIG['user_agent']
    )
    
    print("Testing Reddit connection...")
    print(f"Read-only mode: {reddit.read_only}")
    
    # Test fetching a few posts from r/nyc
    print("\nFetching 3 posts from r/nyc...")
    subreddit = reddit.subreddit('nyc')
    for post in subreddit.hot(limit=3):
        print(f"\nTitle: {post.title}")
        print(f"Score: {post.score}")
        print(f"Comments: {post.num_comments}")
        print(f"URL: {post.url}")
        print("-" * 80)

if __name__ == "__main__":
    test_reddit_connection() 