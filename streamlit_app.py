import streamlit as st
from datetime import datetime
import json
import os
import uuid
from openai import OpenAI

# Create an OpenAI client
openai_api_key = st.secrets["OpenAI_Key"]
system_prompt = st.secrets["prompt"]

# Define a function to interact with OpenAI API
def generate_response(messages):
    client = OpenAI(api_key=openai_api_key)
    stream = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",  # Updated to a more recent model
        messages=messages,  # Now this contains all conversation history
        stream=True,
        temperature=1.3,  # Lowered temperature for more coherent responses
        max_tokens=3000,  # Reduced max tokens to prevent overly long responses
    )
    return stream


# JSON file to store chat logs
chat_log_file = "chat_logs.json"

# Function to load existing chat logs
def load_chat_logs():
    if os.path.exists(chat_log_file):
        with open(chat_log_file, "r") as file:
            return json.load(file)
    return {}

# Function to save chat logs
def save_chat_logs(chat_logs):
    with open(chat_log_file, "w") as file:
        json.dump(chat_logs, file, indent=4)

# Function to get or create a user session
def get_user_session():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

# Function to load user messages from chat logs
def load_user_messages(user_id, chat_logs):
    return chat_logs.get(user_id, [])

# Function to save user messages to chat logs
def save_user_messages(user_id, messages, chat_logs):
    chat_logs[user_id] = messages
    save_chat_logs(chat_logs)

# Load existing chat logs
chat_logs = load_chat_logs()

# Get or create a user session
user_id = get_user_session()

# Load user messages from chat logs
if "messages" not in st.session_state:
    st.session_state.messages = load_user_messages(user_id, chat_logs)

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a chat input field
if user_input := st.chat_input("Décrivez votre projet ou le type de données dont vous avez besoin"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare full conversation history including system prompt
    full_conversation = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # Generate a response using the OpenAI API
    stream = generate_response(full_conversation)

    # Display assistant response
    with st.chat_message("assistant"):
        response = st.empty()
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                response.markdown(full_response)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Save the messages to the chat logs
    save_user_messages(user_id, st.session_state.messages, chat_logs)
