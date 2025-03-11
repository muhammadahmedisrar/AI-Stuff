import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display
# from openai import OpenAI


# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_ROUTER_API_KEY')

# Check the key
if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")


# openai = OpenAI()
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Define the request headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

user_prompt = input("Please enter your prompt: ")

# Define the request payload
payload = {
    "model": "openai/gpt-4o",  # Example model (you can change to others like "deepseek", "llama3-70b", etc.)
    "messages": [
        {
          "role": "system",
          "content": [
            {
              "type": "text",
              "text": "You are an expert of the book kite runners by khalid Husseny."
            }
            # {
            #   "type": "text",
            #   "text": "HUGE TEXT BODY",
            #   "cache_control": {
            #     "type": "ephemeral"
            #   }
            # }
          ]
        },
        {"role": "user", "content": user_prompt}],
    "max_tokens": 100  # Limits the response length
}

# Make the API request
response = requests.post(API_URL, json=payload, headers=headers)

# Print the response
if response.status_code == 200:
    print("Response:", response.json()["choices"][0]["message"]["content"])
else:
    print("Error:", response.status_code, response.text)