import os
from anthropic import Anthropic

key = os.environ.get("ANTHROPIC_API_KEY")
print("Key found:", repr(key))

if not key:
    print("ERROR: No key found in environment. Stopping here.")
else:
    client = Anthropic(api_key=key)
    print("Client created successfully.")