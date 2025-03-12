#establish some ground rules for exmaple if model doesnt know something it should say so instead of hallucinating 
#provide critical background context 

#context building 
#during conversation insert context to give more relevant background information for the topic 

#multishot prompting to train on conversational style and scenarios by providing relevant conversations 
#this is kind of training but also not exactly training by just giving examples its predictions gets strong to get better next token 



# chat(message, history)

# Which expects to receive history in a particular format, which we need to map to the OpenAI format before we call OpenAI:

# [
#     {"role": "system", "content": "system message here"},
#     {"role": "user", "content": "first user prompt here"},
#     {"role": "assistant", "content": "the assistant's response"},
#     {"role": "user", "content": "the new user prompt"},
# ]
# But Gradio has been upgraded! Now it will pass in history in the exact OpenAI format, perfect for us to send straight to OpenAI.

# So our work just got easier!

# We will write a function chat(message, history) where:
# message is the prompt to use
# history is the past conversation, in OpenAI format

# We will combine the system message, history and latest message, then call OpenAI.

#imports 
import os
from dotenv import load_dotenv
import gradio as gr
import re
import ollama

# Initialize
MODEL = "llama3.2"


system_message = "You are a funny, saarcastic and humorous chat bot, that chats with \
the user about life in a fun way. You give answers to all the question this way. You are also \
a huge The office sitcom fan and will try to imitate its actors from time to time \
You will also say thats what she said alot \
For example when a user asks about the meaning of depression you give it the \
answer that dwight gave saying its just a fancy way of feeling bumped out"

system_message += "\nDo also try to keep the answers good and informative as well"


def chat(message, history):
  relevant_system_message = system_message

  messages = [{"role": "system", "content": relevant_system_message}] + history + [{"role": "user", "content": message}]

  
  print("History is:")
  print(history)
  print("And messages is:")
  print(messages)

  stream = ollama.chat(model=MODEL, messages=messages, stream=True)

  response = ""
  for chunk in stream:
    response += chunk['message']['content'] or ''
    yield response

gr.ChatInterface(fn=chat, type="messages").launch()