#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
import openai
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Initialize OpenAI client
        client = openai.OpenAI()
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=5
        )
        
        # Only log success/failure, not the actual response content
        logger.info("✅ OpenAI API Connection Successful")
        return True
    except Exception as e:
        # Log error type but not the full error message which might contain sensitive info
        error_type = type(e).__name__
        logger.error(f"❌ OpenAI API Connection Failed: {error_type}")
        return False

def main():
    """Run OpenAI API connection test."""
    logger.info("Starting OpenAI API Connection Test...")
    
    # Test OpenAI API
    success = test_openai_connection()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"OpenAI API: {'✅ Success' if success else '❌ Failed'}")

if __name__ == "__main__":
    main() 