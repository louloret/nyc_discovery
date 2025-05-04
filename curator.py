import openai
from typing import List, Dict, Any
from config import OPENAI_API_KEY, CURATION_PROMPT

class NYCCurator:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

    def create_themed_day_plan(self, items: List[Dict[str, Any]], theme: str = None) -> Dict[str, Any]:
        """Create a themed day plan using the given items."""
        # Filter items by theme if provided
        if theme:
            filtered_items = [
                item for item in items
                if theme.lower() in [vibe.lower() for vibe in item.get('vibes', [])]
            ]
        else:
            filtered_items = items

        # Format items for the prompt
        formatted_items = []
        for item in filtered_items:
            item_info = {
                'name': item.get('title') or item.get('name') or 'Untitled',
                'category': item.get('category', 'Unknown'),
                'vibes': item.get('vibes', []),
                'description': item.get('content') or item.get('description') or '',
                'location': item.get('venue') or 'Location not specified',
                'time': item.get('start_time') or 'Time not specified',
                'price': item.get('price') or 'Price not specified'
            }
            formatted_items.append(item_info)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative NYC experience curator."},
                    {"role": "user", "content": CURATION_PROMPT.format(items=formatted_items)}
                ],
                temperature=0.7
            )
            
            return {
                'theme': theme or 'General NYC Experience',
                'plan': response.choices[0].message.content,
                'items_used': formatted_items
            }
            
        except Exception as e:
            print(f"Error in creating day plan: {str(e)}")
            return {
                'theme': theme or 'General NYC Experience',
                'plan': "Unable to generate plan at this time.",
                'items_used': []
            }

    def create_interactive_map(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an interactive map with all items."""
        # This is a simplified version - in practice, you'd want to use a proper mapping service
        map_points = []
        
        for item in items:
            if 'venue' in item or 'location' in item:
                point = {
                    'name': item.get('title') or item.get('name') or 'Untitled',
                    'category': item.get('category', 'Unknown'),
                    'location': item.get('venue') or item.get('location'),
                    'description': item.get('content') or item.get('description') or '',
                    'url': item.get('url', '')
                }
                map_points.append(point)
        
        return {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': point,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [0, 0]  # In practice, you'd want to geocode the location
                    }
                }
                for point in map_points
            ]
        }

    def generate_recommendations(self, items: List[Dict[str, Any]], 
                               categories: List[str] = None,
                               vibes: List[str] = None) -> Dict[str, Any]:
        """Generate recommendations based on categories and vibes."""
        # Filter items
        filtered_items = items
        
        if categories:
            filtered_items = [
                item for item in filtered_items
                if item.get('category') in categories
            ]
        
        if vibes:
            filtered_items = [
                item for item in filtered_items
                if any(vibe in item.get('vibes', []) for vibe in vibes)
            ]
        
        # Create recommendations for different time slots
        morning_items = [item for item in filtered_items if 'morning' in item.get('vibes', [])]
        afternoon_items = [item for item in filtered_items if 'afternoon' in item.get('vibes', [])]
        evening_items = [item for item in filtered_items if 'nightlife' in item.get('category', '')]
        
        return {
            'morning': self.create_themed_day_plan(morning_items, 'Morning Activities'),
            'afternoon': self.create_themed_day_plan(afternoon_items, 'Afternoon Activities'),
            'evening': self.create_themed_day_plan(evening_items, 'Evening Activities'),
            'map': self.create_interactive_map(filtered_items)
        } 