import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

print("Key loaded:", bool(api_key))
if api_key:
    print("Key starts with:", api_key[:5] + "... (hidden)")
else:
    print("Key not found.") 