import openai
from typing import List, Dict, Any
from config import OPENAI_API_KEY, CATEGORIES, VIBES, CLASSIFICATION_PROMPT
import json

class NYCClassifier:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

    def classify_content(self, content: str) -> Dict[str, Any]:
        """Classify content into categories and tag with vibes using OpenAI."""
        prompt = CLASSIFICATION_PROMPT.format(
            categories=', '.join(CATEGORIES),
            vibes=', '.join(VIBES),
            content=content
        )
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies NYC-related content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Parse the response
            result = response.choices[0].message.content
            try:
                classification = json.loads(result)
                return classification
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'category': 'Unknown',
                    'vibes': [],
                    'confidence_score': 0.0
                }
                
        except Exception as e:
            print(f"Error in classification: {str(e)}")
            return {
                'category': 'Error',
                'vibes': [],
                'confidence_score': 0.0
            }

    def process_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of items and add classification data."""
        classified_items = []
        
        for item in items:
            # Combine relevant text for classification
            content = ""
            if 'title' in item:
                content += item['title'] + "\n"
            if 'content' in item:
                content += item['content'] + "\n"
            if 'description' in item:
                content += item['description'] + "\n"
            if 'caption' in item:
                content += item['caption'] + "\n"
            
            # Get classification
            classification = self.classify_content(content)
            
            # Add classification to item
            item.update({
                'category': classification['category'],
                'vibes': classification['vibes'],
                'confidence_score': classification['confidence_score']
            })
            
            classified_items.append(item)
        
        return classified_items 