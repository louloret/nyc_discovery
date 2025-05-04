import json
from datetime import datetime
from scraper import NYCScraper
from classifier import NYCClassifier
from ranker import NYCRanker
from curator import NYCCurator

def save_results(data: dict, filename: str = None):
    """Save results to a JSON file."""
    if filename is None:
        filename = f"nyc_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    # Initialize components
    scraper = NYCScraper()
    classifier = NYCClassifier()
    ranker = NYCRanker()
    curator = NYCCurator()
    
    print("Starting NYC Discovery Agent...")
    
    # Step 1: Scrape data
    print("Scraping data from various sources...")
    items = scraper.scrape_all()
    print(f"Found {len(items)} items")
    
    # Step 2: Classify items
    print("Classifying items...")
    classified_items = classifier.process_batch(items)
    
    # Step 3: Rank items
    print("Ranking items...")
    ranked_items = ranker.rank_items(classified_items)
    
    # Step 4: Generate recommendations
    print("Generating recommendations...")
    recommendations = curator.generate_recommendations(
        ranked_items,
        categories=['Art', 'Food', 'Nightlife'],
        vibes=['quirky', 'intellectual']
    )
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_items': len(ranked_items),
        'ranked_items': ranked_items,
        'recommendations': recommendations
    }
    
    save_results(results)
    print("Results saved to file")
    
    # Print summary
    print("\nSummary:")
    print(f"Total items discovered: {len(ranked_items)}")
    print("\nTop 5 items:")
    for i, item in enumerate(ranked_items[:5], 1):
        print(f"{i}. {item.get('title') or item.get('name')} (Score: {item['final_score']:.2f})")
    
    print("\nThemed day plans generated:")
    for time_slot in ['morning', 'afternoon', 'evening']:
        print(f"- {time_slot.capitalize()} activities")

if __name__ == "__main__":
    main() 