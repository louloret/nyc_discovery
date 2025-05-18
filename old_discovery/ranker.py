from typing import List, Dict, Any
from datetime import datetime
from config import RANKING_WEIGHTS

class NYCRanker:
    def __init__(self):
        self.weights = RANKING_WEIGHTS

    def calculate_originality_score(self, item: Dict[str, Any], all_items: List[Dict[str, Any]]) -> float:
        """Calculate how unique/novel an item is compared to others."""
        # This is a simplified version - in practice, you'd want to use embeddings
        # and calculate similarity scores
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        # Count how many times similar words appear in other items
        similar_count = 0
        for other in all_items:
            if other != item:
                other_title = other.get('title', '').lower()
                other_content = other.get('content', '').lower()
                
                # Simple word overlap check
                title_words = set(title.split())
                other_title_words = set(other_title.split())
                content_words = set(content.split())
                other_content_words = set(other_content.split())
                
                if (len(title_words & other_title_words) > 2 or 
                    len(content_words & other_content_words) > 5):
                    similar_count += 1
        
        # More unique items get higher scores
        return 1.0 - (similar_count / len(all_items))

    def calculate_social_proof_score(self, item: Dict[str, Any]) -> float:
        """Calculate score based on social engagement."""
        score = 0.0
        
        # Reddit metrics
        if item['source'] == 'reddit':
            score = (item['score'] / 1000) + (item['num_comments'] / 100)
        
        # Instagram metrics (simplified)
        elif item['source'] == 'instagram':
            # In practice, you'd want to get actual like/comment counts
            score = 0.5  # Placeholder
        
        # Eventbrite metrics
        elif item['source'] == 'eventbrite':
            # In practice, you'd want to get actual attendance/interest metrics
            score = 0.5  # Placeholder
        
        return min(score, 1.0)  # Cap at 1.0

    def calculate_freshness_score(self, item: Dict[str, Any]) -> float:
        """Calculate how recent/current an item is."""
        now = datetime.now()
        
        if 'created_utc' in item:
            created = datetime.fromtimestamp(item['created_utc'])
            days_old = (now - created).days
        elif 'timestamp' in item:
            created = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            days_old = (now - created).days
        elif 'start_time' in item:
            created = datetime.fromisoformat(item['start_time'])
            days_old = (now - created).days
        else:
            return 0.5  # Default score if no timestamp available
        
        # Score decreases with age, but not linearly
        return max(0.0, 1.0 - (days_old / 30))

    def calculate_accessibility_score(self, item: Dict[str, Any]) -> float:
        """Calculate how accessible an item is."""
        score = 1.0
        
        # Check for price information
        if 'price' in item and item['price'] is not None:
            # Adjust score based on price (lower is better)
            price = float(item['price'])
            if price > 50:
                score *= 0.5
            elif price > 100:
                score *= 0.3
        
        # Check for time information
        if 'start_time' in item and 'end_time' in item:
            # Events with specific times are more accessible
            score *= 1.2
        
        return min(score, 1.0)

    def rank_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate final scores and rank items."""
        for item in items:
            # Calculate individual scores
            originality = self.calculate_originality_score(item, items)
            social_proof = self.calculate_social_proof_score(item)
            freshness = self.calculate_freshness_score(item)
            accessibility = self.calculate_accessibility_score(item)
            
            # Calculate weighted score
            final_score = (
                originality * self.weights['originality'] +
                social_proof * self.weights['social_proof'] +
                freshness * self.weights['freshness'] +
                accessibility * self.weights['accessibility']
            )
            
            # Add scores to item
            item.update({
                'originality_score': originality,
                'social_proof_score': social_proof,
                'freshness_score': freshness,
                'accessibility_score': accessibility,
                'final_score': final_score
            })
        
        # Sort by final score
        return sorted(items, key=lambda x: x['final_score'], reverse=True) 