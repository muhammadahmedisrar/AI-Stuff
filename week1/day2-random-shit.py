import ollama 

# Constants
MODEL = "llama3.2"

messages = [
    {"role": "user", "content": "Describe some of the business applications of Generative AI"}
]

response = ollama.chat(model=MODEL, messages=messages)
print(response['message']['content'])