import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
import os
import uuid
import streamlit as st
from openai import OpenAI

# Create an OpenAI client
openai_api_key = st.secrets["OpenAI_Key"]
system_prompt = st.secrets["prompt"]

st.title("🔍 Data Finder - Chatbot")
st.write(
    """Bonjour à tous,    
    """
)
st.write(
    "Pendant mon stage, j’ai constaté que l’accès aux données dans l’entreprise était souvent complexe, avec des informations dispersées sur plusieurs plateformes et nécessitant divers intermédiaires. Data Finder a pour objectif de centraliser ces données et de vous indiquer où elles se trouvent pour simplifier votre travail."
)

st.write(
    "Avez-vous déjà utilisé Data Finder ? Vos retours me seraient très précieux pour continuer à améliorer l’outil. N’hésitez pas à me contacter à [mon adresse email](mailto:alexandre.ruffierdepenoux@essec.edu) pour partager vos impressions et suggestions."
)

st.write(
    "P.S. : Les données fournies par Data Finder sont fictives et servent uniquement à illustrer son fonctionnement, afin de vous permettre de mieux comprendre son potentiel."
)

previous_message_id = None  # This will hold the message ID of the previous email

# Define the function to send the email with the JSON data
def send_email_with_json(chat_logs):
    global previous_message_id  # Use the global variable to track the thread

    # Convert chat logs to JSON format and handle Unicode characters
    json_data = json.dumps(chat_logs, indent=4, ensure_ascii=False)

    # Email variables
    sender_email = 'alex.depenoux@gmail.com'
    sender_name = 'DataFinder - Chat Report'
    recipient_email = 'alex.depenoux@gmail.com'
    subject = 'Chat Logs JSON File Attached'
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'alex.depenoux@gmail.com'
    smtp_password = 'sqyj tcam uivt gzbe'  # Replace this with the actual password or use OAuth if available

    # HTML content for the email body
    html_content = """
    <html>
      <body>
        <p>Hello Alexandre,</p>
        <p>Please find the attached JSON data containing the chat logs.</p>
        <p>Best regards,<br>Alex Depenoux</p>
      </body>
    </html>
    """

    # Create the multipart message
    msg = MIMEMultipart()
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the HTML content
    msg.attach(MIMEText(html_content, 'html'))

    # Attach the JSON data as a file
    json_attachment = MIMEApplication(json_data, _subtype="json")
    json_attachment.add_header('Content-Disposition', 'attachment', filename='chat_logs.json')
    msg.attach(json_attachment)

    # Handle threading (reply to the previous message)
    if previous_message_id:
        msg.add_header('In-Reply-To', previous_message_id)
        msg.add_header('References', previous_message_id)

    # Send the email via the SMTP server
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        # Send the email and capture the Message-ID of the sent email
        response = server.sendmail(sender_email, recipient_email, msg.as_string())
        previous_message_id = msg['Message-ID']  # Save the Message-ID for threading the next email

# Define a function to interact with OpenAI API
def generate_response(messages):
    client = OpenAI(api_key=openai_api_key)
    stream = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",  # Updated to a more recent model
        messages=messages,  # Now this contains all conversation history
        stream=True,
        temperature=1.05,  # Lowered temperature for more coherent responses
        max_tokens=3000,  # Reduced max tokens to prevent overly long responses
    )
    return stream

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

# Initialize an empty dictionary for chat logs
chat_logs = {}

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

    # Save the messages to the chat logs in-memory
    save_user_messages(user_id, st.session_state.messages, chat_logs)

    # Send the chat logs via email without saving to a file
    send_email_with_json(chat_logs)
